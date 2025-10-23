# app/services/face_capture_service.py
import cv2
import numpy as np
from datetime import datetime
from sqlalchemy.orm import Session
from typing import List
from insightface.app import FaceAnalysis
from app.model.face import Face

# -------------------- UTILITÁRIOS DE IMAGEM --------------------
def image_to_base64(image: np.ndarray, quality: int = 90) -> str:
    import base64
    from io import BytesIO
    from PIL import Image
    pil = Image.fromarray(image)
    buf = BytesIO()
    pil.save(buf, format="JPEG", quality=quality)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def normalize_image(image: np.ndarray, size=(640, 480)) -> np.ndarray:
    if image.dtype != np.uint8:
        image = (image * 255).astype(np.uint8)
    return cv2.resize(image, size)

# -------------------- PERSISTÊNCIA --------------------
def persist_face(db: Session, user_id: int, filename: str, source: str, embedding: list, image_b64: str) -> Face:
    """
    Cria um registro completo na tabela 'faces' com embedding e imagem.
    """
    face = Face(
        user_id=user_id,
        filename=filename,
        source=source,
        embedding=embedding,
        image_data=image_b64,
        created_at=datetime.utcnow()
    )
    db.add(face)
    db.commit()
    db.refresh(face)
    return face

# -------------------- INICIALIZAÇÃO DO MODELO --------------------
face_app = FaceAnalysis(name="buffalo_l")
face_app.prepare(ctx_id=-1)  # CPU=-1, GPU=0 se disponível

# -------------------- EXTRAÇÃO DE EMBEDDINGS --------------------
def extract_embeddings(image: np.ndarray) -> List[np.ndarray]:
    faces = face_app.get(image)
    if not faces:
        return []
    return [f.embedding for f in faces]

# -------------------- MULTI-FRAMES --------------------
def save_multiple_faces_from_upload(
    db: Session,
    user_id: int,
    files: List[bytes],
    filenames: List[str],
    source: str = "UPLOAD"
):
    """
    Recebe múltiplos arquivos (frames) e salva cada face detectada na tabela 'faces'.
    Cada face terá embedding e imagem base64.
    """
    results = []

    for file_bytes, filename in zip(files, filenames):
        try:
            nparr = np.frombuffer(file_bytes, np.uint8)
            img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img_bgr is None:
                results.append({"filename": filename, "status": "failed", "reason": "Falha ao decodificar a imagem"})
                continue

            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            img_rgb = normalize_image(img_rgb)
            img_b64 = image_to_base64(img_rgb)

            embeddings = extract_embeddings(img_rgb)
            if not embeddings:
                results.append({"filename": filename, "status": "failed", "reason": "Nenhum rosto detectado"})
                continue

            # Salva cada embedding como uma face separada
            saved_faces = []
            for emb in embeddings:
                face = persist_face(
                    db=db,
                    user_id=user_id,
                    filename=filename,
                    source=source,
                    embedding=emb.tolist(),
                    image_b64=img_b64
                )
                saved_faces.append(face.face_id)

            results.append({
                "status": "ok",
                "user_id": user_id,
                "filename": filename,
                "faces_saved": saved_faces
            })

        except Exception as e:
            db.rollback()
            results.append({"filename": filename, "status": "failed", "reason": str(e)})

    return results
