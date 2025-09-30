import cv2

def capture_image(camera_index=0):
    """
    Captura uma imagem da câmera.
    
    :param camera_index: índice da câmera (0 = primeira câmera)
    :return: imagem capturada em bytes (JPEG)
    """
    # Abre a câmera
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError("Não foi possível acessar a câmera")

    # Captura um frame
    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise RuntimeError("Falha ao capturar a imagem")

    # Converte a imagem para JPEG em bytes
    ret, buffer = cv2.imencode(".jpg", frame)
    if not ret:
        raise RuntimeError("Falha ao converter a imagem para JPEG")

    return buffer.tobytes()
