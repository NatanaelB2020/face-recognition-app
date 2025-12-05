import numpy as np
import face_recognition
from typing import Optional


def generate_face_embedding(image_bytes: bytes) -> Optional[np.ndarray]:
    """
    Recebe bytes de imagem e retorna o embedding facial (128D).
    Retorna None caso nenhum rosto seja detectado.
    """

    # Converte bytes para array numpy
    np_img = np.frombuffer(image_bytes, np.uint8)

    # Decodifica com OpenCV
    import cv2
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    if img is None:
        return None

    # Converte para RGB pois o face_recognition usa RGB
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Detecta localização dos rostos
    locations = face_recognition.face_locations(rgb_img)

    if len(locations) == 0:
        return None

    # Extrai embeddings (somente o primeiro rosto)
    encodings = face_recognition.face_encodings(rgb_img, locations)

    if len(encodings) == 0:
        return None

    # Retorna o vetor de 128 floats
    return encodings[0]
