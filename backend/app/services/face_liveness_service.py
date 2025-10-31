import cv2
import numpy as np
import time
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
from numpy.linalg import norm
from sqlalchemy.orm import Session
from app.model.face_liveness_state import FaceLivenessState
from app.model.face import Face
from insightface.app import FaceAnalysis

# ================= Inicializa o modelo =================
try:
    import torch
    use_gpu = torch.cuda.is_available()
except ImportError:
    use_gpu = False

face_app = FaceAnalysis(name="buffalo_l")
face_app.prepare(ctx_id=0 if use_gpu else -1, det_size=(320, 320))  # det_size menor para acelerar

user_states = {}
user_states_lock = Lock()

# ================= Parâmetros =================
MOVE_THRESHOLD = 25
STABLE_SIZE_VARIATION = 0.15
STABLE_FRAMES_REQUIRED = 3
CENTER_TOLERANCE = 0.20
FACE_MATCH_THRESHOLD = 0.65
BATCH_MATCH_RATIO = 0.6

# ----------------- Redução de resolução -----------------
def resize_for_face_detection(img, target_width=320):
    h, w = img.shape[:2]
    scale = target_width / w
    return cv2.resize(img, (target_width, int(h * scale)))

# ================= SERVIÇO =================
class FaceLivenessService:
    """Serviço principal de verificação de liveness facial."""

    # ----------------- Similaridade -----------------
    @staticmethod
    def compute_similarity(emb1, emb2):
        if emb1 is None or emb2 is None:
            return 0.0
        return float(np.dot(emb1, emb2) / (norm(emb1) * norm(emb2)))

    # ----------------- Centralização -----------------
    @staticmethod
    def is_centered(bbox, img_shape):
        x_center = (bbox[0] + bbox[2]) / 2
        y_center = (bbox[1] + bbox[3]) / 2
        dx = abs(x_center - img_shape[1] / 2) / (img_shape[1] / 2)
        dy = abs(y_center - img_shape[0] / 2) / (img_shape[0] / 2)
        return dx <= CENTER_TOLERANCE and dy <= CENTER_TOLERANCE

    # ----------------- Movimento -----------------
    @staticmethod
    def detect_head_movement(state, curr_bbox):
        prev_bbox = state.get("prev_bbox")
        if prev_bbox is None:
            state.update({"prev_bbox": curr_bbox, "stable_frames": 0, "consistent_dir": None})
            return None

        dx = ((curr_bbox[0] + curr_bbox[2]) / 2) - ((prev_bbox[0] + prev_bbox[2]) / 2)
        prev_width = prev_bbox[2] - prev_bbox[0]
        curr_width = curr_bbox[2] - curr_bbox[0]
        size_ratio = abs(curr_width - prev_width) / prev_width

        if size_ratio > STABLE_SIZE_VARIATION:
            state.update({"stable_frames": 0, "consistent_dir": None, "prev_bbox": curr_bbox})
            return None

        direction = "DIREITA" if dx > MOVE_THRESHOLD else "ESQUERDA" if dx < -MOVE_THRESHOLD else None

        if direction:
            if direction == state.get("consistent_dir"):
                state["stable_frames"] += 1
            else:
                state.update({"consistent_dir": direction, "stable_frames": 1})

            if state["stable_frames"] >= STABLE_FRAMES_REQUIRED:
                state.update({"stable_frames": 0, "prev_bbox": curr_bbox})
                return direction

        state["prev_bbox"] = curr_bbox
        return None

    # ----------------- Processa 1 frame (otimizado) -----------------
    @staticmethod
    def process_frame(db: Session, user_id: int, frame_bytes: bytes, faces_db_embeddings=None):
        np_arr = np.frombuffer(frame_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        img_small = resize_for_face_detection(img)
        faces = face_app.get(img_small)

        if not faces:
            return {"status": "no_face_detected", "message": "Nenhum rosto detectado"}

        curr_face = faces[0]
        curr_emb = np.array(curr_face.embedding, dtype=np.float32)

        # Carrega embeddings do banco apenas uma vez
        if faces_db_embeddings is None:
            faces_db = db.query(Face).filter(Face.user_id == user_id).all()
            if not faces_db:
                return {"status": "error", "message": "Nenhuma face registrada para este usuário"}
            faces_db_embeddings = [(f, np.array(f.embedding, dtype=np.float32)) for f in faces_db]

        # Seleciona a face mais semelhante
        best_face, best_score = max(
            ((f, FaceLivenessService.compute_similarity(e, curr_emb)) for f, e in faces_db_embeddings),
            key=lambda x: x[1]
        )

        same_person = best_score >= FACE_MATCH_THRESHOLD
        return {"status": "ok", "best_similarity": best_score, "same_person": same_person}

    # ----------------- Processa lote otimizado para 20 frames -----------------
    @staticmethod
    def process_batch_frames(db: Session, user_id: int, frame_list: list[bytes]):
        print("\n[PROCESSO] Iniciando verificação de vivacidade facial...")
        start_time = time.time()

        # Pré-carrega embeddings do usuário (1x)
        faces_db = db.query(Face).filter(Face.user_id == user_id).all()
        if not faces_db:
            print("[ERRO] Nenhuma face registrada para este usuário")
            return {"status": "error", "message": "Nenhuma face registrada"}

        faces_db_embeddings = [(f, np.array(f.embedding, dtype=np.float32)) for f in faces_db]

        # ----------------- Analisa todos os frames -----------------
        selected_frames = frame_list  

        # ----------------- Função auxiliar para processar 1 frame -----------------
        def process_frame_bytes(frame_bytes):
            np_arr = np.frombuffer(frame_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            img_small = resize_for_face_detection(img)
            faces = face_app.get(img_small)
            if not faces:
                return None

            curr_face = faces[0]
            curr_emb = np.array(curr_face.embedding, dtype=np.float32)

            # Seleciona a face mais semelhante
            best_face, best_score = max(
                ((f, FaceLivenessService.compute_similarity(e, curr_emb)) for f, e in faces_db_embeddings),
                key=lambda x: x[1]
            )
            return best_score

        # ----------------- Processamento paralelo -----------------
        max_workers = min(6, len(selected_frames))  # usa até 6 threads
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            similarities = list(filter(None, executor.map(process_frame_bytes, selected_frames)))

        if not similarities:
            print("[ERRO] Nenhum rosto válido detectado durante o processamento.")
            return {"status": "error", "message": "Nenhum rosto válido detectado"}

        match_ratio = sum(s >= FACE_MATCH_THRESHOLD for s in similarities) / len(similarities)
        avg_similarity = np.mean(similarities)
        same_person_batch = match_ratio >= BATCH_MATCH_RATIO
        total_time = time.time() - start_time

        # ----------------- LOG FINAL -----------------
        print("\n========= RESULTADO FINAL =========")
        print(f"Total de frames analisados: {len(selected_frames)}")
        print(f"Média de similaridade: {avg_similarity * 100:.2f}%")
        print(f"Taxa de correspondência: {match_ratio * 100:.2f}%")
        print(f"Pessoa reconhecida: {'SIM' if same_person_batch else 'NÃO'}")
        print(f"Tempo total de processamento: {total_time:.2f} segundos")
        print("===================================\n")

        return {
            "status": "ok",
            "same_person_batch": same_person_batch,
            "matching_ratio": match_ratio,
            "average_similarity": avg_similarity,
            "processing_time": total_time,
            "batch_message": (
                f"Rosto {'correto' if same_person_batch else 'diferente'} "
                f"({match_ratio * 100:.0f}% dos frames, média {avg_similarity * 100:.1f}%)"
            ),
        }
