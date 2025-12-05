import cv2
import numpy as np
from app.model.face import Face
from insightface.app import FaceAnalysis


# ============================================================
#  DETECÇÃO AUTOMÁTICA DE GPU
# ------------------------------------------------------------
#  insightface utiliza ctx_id para decidir se roda na GPU (CUDA)
#    ctx_id = -1 → CPU
#    ctx_id = 0  → GPU device 0
#  Aqui testamos automaticamente se existe GPU CUDA disponível.
# ============================================================

def detect_gpu():
    try:
        # Tentativa simples para verificar presença das GPUs CUDA
        import torch
        if torch.cuda.is_available():
            return 0  # GPU ID 0
    except Exception:
        pass
    return -1         # fallback → CPU


CTX_ID = detect_gpu()  
face_app = FaceAnalysis(name="buffalo_l")
face_app.prepare(ctx_id=CTX_ID)   # inicializa CPU ou GPU de acordo com CTX_ID


# ============================================================
#  SAVE MULTIPLE FACES WITH AUTO-GPU
# ------------------------------------------------------------
#  Este método:
#   - Lê múltiplos arquivos enviados
#   - Converte para matriz OpenCV
#   - Detecta faces com InsightFace
#   - Extrai o embedding da maior face
#   - Salva no banco com SQLAlchemy
#   - Retorna lista com resultados individuais
# ============================================================

async def save_multiple_faces_from_upload(db, user_id: int, files):
    results = []             # Feedback por arquivo
    objects_to_save = []     # Objetos ORM a serem salvos no final em batch

    # ------------------------------------------------------------
    # LER TODOS OS ARQUIVOS EM MEMÓRIA (assíncrono, eficiente)
    # ------------------------------------------------------------
    contents = [await f.read() for f in files]

    # ------------------------------------------------------------
    # DECODIFICAR IMAGENS USANDO OPENCV
    # cv2.imdecode → transforma bytes em matriz BGR
    # ------------------------------------------------------------
    imgs = [
        cv2.imdecode(np.frombuffer(c, np.uint8), cv2.IMREAD_COLOR)
        for c in contents
    ]

    # ------------------------------------------------------------
    # LOOP PARA TRATAR CADA ARQUIVO E SUA IMAGEM
    # ------------------------------------------------------------
    for file, img in zip(files, imgs):
        try:
            if img is None:
                results.append({
                    "file": file.filename,
                    "status": "error",
                    "message": "unable to decode image"
                })
                continue

            # ------------------------------------------------------------
            # DETECÇÃO DE FACES COM INSIGHTFACE
            # face_app.get(img) → retorna várias faces, com bbox + embedding
            # ------------------------------------------------------------
            faces = face_app.get(img)

            if not faces:
                results.append({
                    "file": file.filename,
                    "status": "error",
                    "message": "no face detected"
                })
                continue

            # ------------------------------------------------------------
            # ESCOLHE A MAIOR FACE
            # bbox formato: [x1, y1, x2, y2]
            # maior largura = x2 - x1
            # ------------------------------------------------------------
            main_face = max(faces, key=lambda f: f.bbox[2] - f.bbox[0])

            # ------------------------------------------------------------
            # EXTRAÇÃO DO EMBEDDING
            # embedding é um vetor de 512 floats gerado pela rede neural
            # ------------------------------------------------------------
            embedding = main_face.embedding.tolist()

            # ------------------------------------------------------------
            # CRIA OBJETO ORM (SQLAlchemy)
            # ------------------------------------------------------------
            new_face = Face(
                user_id=user_id,
                filename=file.filename,
                source="UPLOAD",
                embedding=embedding
            )

            # Adicionado para commit em batch (melhor performance)
            objects_to_save.append(new_face)

            results.append({"file": file.filename, "status": "ok"})

        except Exception as e:
            # Qualquer erro inesperado é retornado ao cliente
            results.append({
                "file": file.filename,
                "status": "error",
                "message": str(e)
            })

    # ------------------------------------------------------------
    # SALVA TODOS DE UMA VEZ — ganho de performance massivo
    # ------------------------------------------------------------
    if objects_to_save:
        db.add_all(objects_to_save)
        db.commit()

    return results
