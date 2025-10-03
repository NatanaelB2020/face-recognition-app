import cv2
import numpy as np
from sqlalchemy.orm import Session
from app.services.face_service import get_face_by_id, extract_embedding
from app.services.capture_image import find_matching_face
import mediapipe as mp

mp_face_mesh = mp.solutions.face_mesh

def check_face_liveness_visual(
    db: Session,
    user_id: int,
    face_id: int,
    threshold: float = 0.8,
    movements_required: int = 3,
    frames_to_capture: int = 20
) -> dict:
    """
    Liveness ativo com MediaPipe + OpenCV mostrando setas de movimento da cabeça
    - Detecta movimentos leves para os lados, cima e baixo
    """
    reference_face = get_face_by_id(db, user_id, face_id)
    if not reference_face:
        return {"match": False, "score": 0.0, "user_id": user_id, "face_id": face_id, "message": "Face de referência não encontrada"}

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Não foi possível abrir a câmera")

    yaw_seq, pitch_seq, roll_seq = [], [], []
    prev_yaw, prev_pitch, prev_roll = 0.0, 0.0, 0.0
    result = {"score": 0.0, "match": False}

    with mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as face_mesh:

        for _ in range(frames_to_capture):
            ret, frame = cap.read()
            if not ret:
                continue

            img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_results = face_mesh.process(img_rgb)

            if not mp_results.multi_face_landmarks:
                cv2.imshow("Movimentos da Cabeça", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
                continue

            landmarks = mp_results.multi_face_landmarks[0].landmark

            # --- Calcular yaw, pitch, roll ---
            left_x = np.mean([landmarks[i].x for i in [33, 133, 160]])
            right_x = np.mean([landmarks[i].x for i in [362, 263, 387]])
            yaw = right_x - left_x
            yaw_seq.append(yaw)

            top_y = np.mean([landmarks[i].y for i in [10, 159]])
            bottom_y = np.mean([landmarks[i].y for i in [152, 17]])
            pitch = bottom_y - top_y
            pitch_seq.append(pitch)

            left_eye_y = np.mean([landmarks[i].y for i in [33, 133]])
            right_eye_y = np.mean([landmarks[i].y for i in [362, 263]])
            roll = right_eye_y - left_eye_y
            roll_seq.append(roll)

            # --- Comparar embedding ---
            embedding = extract_embedding(img_rgb)
            if embedding is not None:
                result = find_matching_face(
                    db=db,
                    user_id=user_id,
                    face_id=face_id,
                    embedding=embedding,
                    threshold=threshold
                )

            # --- Visualização ---
            h, w, _ = frame.shape
            center = (w // 2, h // 2)
            arrow_x = int((yaw - prev_yaw) * w * 5)
            arrow_y = int((pitch - prev_pitch) * h * 5)

            cv2.arrowedLine(
                frame,
                center,
                (center[0] + arrow_x, center[1] + arrow_y),
                (0, 255, 0),
                3,
                tipLength=0.2
            )

            cv2.putText(frame, f"Yaw: {yaw:.3f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
            cv2.putText(frame, f"Pitch: {pitch:.3f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
            cv2.putText(frame, f"Roll: {roll:.3f}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

            cv2.imshow("Movimentos da Cabeça", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            prev_yaw, prev_pitch, prev_roll = yaw, pitch, roll

    cap.release()
    cv2.destroyAllWindows()

    # --- Contar movimentos simples (delta menor, mais sensível) ---
    def count_movements(seq, delta=0.005):
        moves = 0
        for i in range(1, len(seq)):
            if abs(seq[i] - seq[i-1]) > delta:
                moves += 1
        return moves

    yaw_moves = count_movements(yaw_seq)
    pitch_moves = count_movements(pitch_seq)
    roll_moves = count_movements(roll_seq)
    total_moves = yaw_moves + pitch_moves + roll_moves

    if total_moves >= movements_required:
        result["match"] = True
        result["message"] = f"Liveness confirmado ({total_moves}/{movements_required} movimentos detectados)"
    else:
        result["match"] = False
        result["message"] = f"Movimentos insuficientes ({total_moves}/{movements_required})"

    return {
        "match": result.get("match", False),
        "score": result.get("score", 0.0),
        "user_id": user_id,
        "face_id": face_id,
        "message": result.get("message", "")
    }
