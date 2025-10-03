# app/services/capture_image.py
import cv2
import numpy as np
from sqlalchemy.orm import Session
from app.model.face import Face


def capture_image() -> np.ndarray:
    """
    Captura uma imagem da webcam usando OpenCV.
    Retorna a imagem em RGB (numpy array).
    """
    print("==> capture_image: Abrindo câmera...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Não foi possível abrir a câmera")

    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise RuntimeError("Falha ao capturar imagem da câmera")

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    print(f"DEBUG: Captura RGB shape: {rgb_frame.shape}, dtype={rgb_frame.dtype}")
    return rgb_frame


# ---------------------------
# Funções de similaridade
# ---------------------------
def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def euclidean_distance(vec1: np.ndarray, vec2: np.ndarray) -> float:
    return np.linalg.norm(vec1 - vec2)


# ---------------------------
# Reconhecimento facial
# ---------------------------
def find_matching_face(
    db: Session,
    user_id: int,
    face_id: int,
    embedding: list[float],
    threshold: float = 0.35,
    metric: str = "cosine"
):
    """
    Compara embedding capturado com o embedding salvo de um usuário específico.
    Retorna dict com resultado do reconhecimento.
    """

    db_face = db.query(Face).filter(
        Face.user_id == user_id,
        Face.id == face_id
    ).first()

    if not db_face or not db_face.embedding:
        return {"match": False, "score": None, "message": "Face não encontrada no banco"}

    db_embedding = np.array(db_face.embedding, dtype=np.float32)
    embedding_np = np.array(embedding, dtype=np.float32)

    # Calcula similaridade/distância
    if metric == "cosine":
        score = cosine_similarity(embedding_np, db_embedding)
        match = score >= 1 - threshold
    else:
        score = euclidean_distance(embedding_np, db_embedding)
        match = score <= threshold

    return {
        "match": match,
        "score": float(score),
        "user_id": db_face.user_id,
        "face_id": db_face.id
    }
