import base64
import cv2
import numpy as np
from sqlalchemy.orm import Session
from datetime import datetime
from app.model.face import Face
from app.schema.schemas import FaceResponse
import mediapipe as mp

mp_face_mesh = mp.solutions.face_mesh


# ------------------------------
# BLOCO 1: Processamento de imagem
# ------------------------------

def load_image_from_bytes(file_data: bytes) -> np.ndarray:
    """Converte bytes em imagem RGB."""
    np_img = np.frombuffer(file_data, np.uint8)
    img_bgr = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise ValueError("Falha ao decodificar imagem.")
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)


def normalize_image(img_rgb: np.ndarray) -> np.ndarray:
    """Garante formato correto (uint8, 3 canais RGB)."""
    if img_rgb.dtype != np.uint8:
        img_rgb = (img_rgb * 255).astype(np.uint8)
    if len(img_rgb.shape) == 2:  # grayscale
        img_rgb = cv2.cvtColor(img_rgb, cv2.COLOR_GRAY2RGB)
    elif img_rgb.shape[2] != 3:
        raise ValueError("A imagem deve ter 3 canais (RGB).")
    return img_rgb


def image_to_base64(img_rgb: np.ndarray) -> str:
    """Converte imagem RGB para base64 (JPEG)."""
    bgr_frame = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    ret, buffer = cv2.imencode(".jpg", bgr_frame)
    if not ret:
        raise RuntimeError("Falha ao converter imagem para JPEG")
    return base64.b64encode(buffer.tobytes()).decode("utf-8")


# ------------------------------
# BLOCO 2: Extração de embedding
# ------------------------------

def extract_embedding(img_rgb: np.ndarray) -> list[float] | None:
    """
    Extrai embedding do rosto usando MediaPipe Face Mesh.
    Retorna lista de floats (landmarks) ou None se não detectar rosto.
    """
    with mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1) as face_mesh:
        results = face_mesh.process(img_rgb)
        if not results.multi_face_landmarks:
            return None

        face_landmarks = results.multi_face_landmarks[0]
        embedding = []
        for lm in face_landmarks.landmark:
            embedding.extend([lm.x, lm.y, lm.z])

        # Normaliza embedding (opcional)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = (np.array(embedding) / norm).tolist()

        return embedding


# ------------------------------
# BLOCO 3: Persistência no banco
# ------------------------------

def persist_face(
    db: Session,
    user_id: int,
    filename: str,
    source: str,
    image_b64: str,
    embedding: list[float]
) -> FaceResponse:
    """Cria objeto Face e salva no banco."""
    db_face = Face(
        user_id=user_id,
        image_data=image_b64,
        filename=filename,
        source=source,
        embedding=embedding,
        created_at=datetime.utcnow()
    )
    db.add(db_face)
    db.commit()
    db.refresh(db_face)

    return FaceResponse(
        id=db_face.id,
        user_id=db_face.user_id,
        filename=db_face.filename,
        image_base64=db_face.image_data,
        source=db_face.source,
        created_at=db_face.created_at
    )


# ------------------------------
# BLOCO 4: Função principal (orquestração)
# ------------------------------

def save_face(
    db: Session,
    user_id: int,
    filename: str,
    source: str,
    img_rgb: np.ndarray = None,
    file_data: bytes = None
) -> FaceResponse:
    """Função principal: orquestra carregamento, extração e salvamento."""
    if img_rgb is None and file_data:
        img_rgb = load_image_from_bytes(file_data)

    if img_rgb is None:
        raise ValueError("Nenhuma imagem fornecida para salvar.")

    img_rgb = normalize_image(img_rgb)

    embedding = extract_embedding(img_rgb)
    if embedding is None:
        raise ValueError("Nenhum rosto detectado na imagem.")

    image_b64 = image_to_base64(img_rgb)

    return persist_face(db, user_id, filename, source, image_b64, embedding)


# ------------------------------
# BLOCO 5: Recuperação de face
# ------------------------------

def get_face_by_id(db: Session, user_id: int, face_id: int) -> FaceResponse | None:
    """Recupera uma face por ID e retorna como resposta."""
    db_face = db.query(Face).filter(Face.user_id == user_id, Face.id == face_id).first()
    if not db_face:
        return None

    return FaceResponse(
        id=db_face.id,
        user_id=db_face.user_id,
        filename=db_face.filename,
        image_base64=db_face.image_data,
        source=db_face.source,
        created_at=db_face.created_at
    )
