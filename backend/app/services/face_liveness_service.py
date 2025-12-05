import os
import cv2
import numpy as np
import time
from sqlalchemy.orm import Session
from typing import List, Optional
from insightface.app import FaceAnalysis
from app.repository.repository_face import get_embeddings_by_user


# ============================================================
# CONFIGURAÇÕES GERAIS DO SISTEMA
# ============================================================

MODEL_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))

# Otimizações internas do OpenCV
cv2.setUseOptimized(True)
cv2.setNumThreads(2)

# Parâmetros do sistema de detecção e validação
DET_SIZE = 160
FACE_MATCH_THRESHOLD = 0.60   # Similaridade mínima por frame
BATCH_MATCH_RATIO = 0.50      # % mínima de frames aceitos
FRAME_SKIP = 3                # Processa 1 frame a cada 3


# ============================================================
# DETECÇÃO AUTOMÁTICA DE GPU
# ------------------------------------------------------------
# ctx_id = -1 → CPU
# ctx_id = 0  → GPU CUDA 0
# insightface utiliza ctx_id para definir onde rodar o modelo
# ============================================================

def detect_gpu():
    try:
        import torch
        if torch.cuda.is_available():
            return 0
    except Exception:
        pass
    return -1


CTX_ID = detect_gpu()


# ============================================================
# INICIALIZAÇÃO DO FACE ANALYSIS (DETECÇÃO + EMBEDDING)
# ============================================================

def _init_face_app():
    """
    Inicializa o InsightFace com:
      - Modelo buffalo_l (robusto e rápido)
      - root customizado
      - apenas detection + recognition
      - processamento automático em GPU se disponível
    """
    fa = FaceAnalysis(
        name="buffalo_l",
        root=MODEL_ROOT,
        allowed_modules=["detection", "recognition"]
    )
    
    # ctx_id é definido automaticamente (GPU ou CPU)
    fa.prepare(
        ctx_id=CTX_ID,
        det_size=(DET_SIZE, DET_SIZE)
    )
    return fa


# Instância global (carregada 1 vez por worker)
face_app = _init_face_app()


# ============================================================
# CACHE EM MEMÓRIA PARA EMBEDDINGS DE USUÁRIOS
# ------------------------------------------------------------
# user_id → matriz Nx512 com embeddings normalizados
# evita consultas repetidas no banco (grande ganho de performance)
# ============================================================

embedding_cache: dict[int, np.ndarray] = {}


# ============================================================
# FUNÇÕES UTILITÁRIAS
# ============================================================

def decode_frame(data: bytes) -> Optional[np.ndarray]:
    """Converte bytes do frame em matriz BGR usando OpenCV."""
    arr = np.frombuffer(data, np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)

def normalize(v: np.ndarray) -> np.ndarray:
    """Normaliza embedding (L2 norm) para dot product correto."""
    return v / (np.linalg.norm(v) + 1e-10)

def get_user_embeddings(db: Session, user_id: int) -> Optional[np.ndarray]:
    """
    Carrega embeddings do usuário do banco e mantém em cache.
    Cada embedding já é convertido para float32 e normalizado.
    """
    if user_id in embedding_cache:
        return embedding_cache[user_id]

    rows = get_embeddings_by_user(db, user_id)
    if not rows:
        return None

    arr = np.vstack([normalize(np.array(r, dtype=np.float32)) for r in rows])
    embedding_cache[user_id] = arr
    return arr


# ============================================================
# SERVIÇO PRINCIPAL DE LIVENESS E MATCHING POR BATCH
# ============================================================

class FaceLivenessService:

    @staticmethod
    def match_similarity(user_embs: np.ndarray, emb: np.ndarray) -> float:
        """
        Calcula a maior similaridade (dot product) entre o embedding detectado
        e todos os embeddings cadastrados do usuário.
        """
        emb = normalize(emb)
        sims = np.dot(user_embs, emb)
        return float(np.max(sims))

    @staticmethod
    def process_batch_frames(db: Session, user_id: int, frames: List[bytes]):
        """
        Processa um lote de frames para validação facial.

        Fluxo:
        - Carrega embeddings do usuário
        - Itera frames (com skip para performance)
        - Detecta face com InsightFace (GPU se disponível)
        - Extrai embedding do primeiro rosto
        - Calcula similaridade
        - Calcula média final e razão de matches
        """

        t0 = time.time()

        # Carrega embeddings do usuário da base (ou cache)
        user_embs = get_user_embeddings(db, user_id)
        if user_embs is None:
            return {"status": "error", "message": "Nenhuma face cadastrada"}

        similarities = []
        processed = 0

        for i, raw in enumerate(frames):

            # Skip reduz carga (processa +- 30% dos frames)
            if i % FRAME_SKIP != 0:
                continue

            img = decode_frame(raw)
            if img is None:
                continue

            # Detecção com GPU/CPU conforme disponível
            faces = face_app.get(img)
            if not faces:
                continue

            # Pega embedding da primeira face detectada
            emb = np.asarray(faces[0].embedding, dtype=np.float32)

            score = FaceLivenessService.match_similarity(user_embs, emb)
            similarities.append(score)
            processed += 1

        if not similarities:
            return {"status": "error", "message": "Nenhum rosto válido detectado"}

        # Estatísticas finais
        avg_sim = float(np.mean(similarities))
        ratio = sum(s >= FACE_MATCH_THRESHOLD for s in similarities) / len(similarities)
        same = ratio >= BATCH_MATCH_RATIO
        total_time = time.time() - t0

        # Logs para debugging / calibração
        print("\n===== RESULTADO FINAL =====")
        print(f"Avg Similarity : {avg_sim:.4f}")
        print(f"Match Ratio    : {ratio:.4f}")
        print(f"Same Person    : {same}")
        print(f"Processing Time: {total_time:.4f} sec")
        print(f"Frames Analyzed: {len(similarities)}")
        print("===========================\n")

        # Retorno para API
        return {
            "status": "ok",
            "same_person_batch": same,
            "matching_ratio": ratio,
            "average_similarity": avg_sim,
            "processing_time": total_time,
            "frames_analyzed": len(similarities),
        }
