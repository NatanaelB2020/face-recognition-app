import cv2
import numpy as np
from sqlalchemy.orm import Session
from app.model.face import Face

def compute_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    if vec1 is None or vec2 is None:
        return 0.0
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

def verify_face_match(db: Session, user_id: int, face_id: int, frame_bytes: bytes) -> dict:
    np_arr = np.frombuffer(frame_bytes, np.uint8)
    img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img_bgr is None:
        return {"status": "error", "message": "Frame inválido."}

    from app.services.face_capture_service import extract_embeddings
    embeddings = extract_embeddings(img_bgr)
    if not embeddings:
        return {"status": "no_face_detected", "message": "Nenhum rosto detectado."}

    captured_emb = embeddings[0]
    face = db.query(Face).filter(Face.face_id == face_id, Face.user_id == user_id).first()
    if not face:
        return {"status": "error", "message": "Face não encontrada."}

    saved_emb = np.array(face.embedding, dtype=np.float32)
    score = compute_cosine_similarity(captured_emb, saved_emb)
    match = score >= 0.6
    return {
        "status": "ok" if match else "mismatch",
        "match": match,
        "score": score,
        "message": "Rosto reconhecido." if match else "Rosto não corresponde."
    }
