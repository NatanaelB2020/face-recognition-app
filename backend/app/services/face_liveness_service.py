import cv2
import numpy as np
import time
from threading import Lock
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
if use_gpu:
    print("[INIT] GPU detectada. Usando aceleração CUDA.")
    face_app.prepare(ctx_id=0, det_size=(640, 640))
else:
    print("[INIT] GPU não detectada. Usando CPU com otimizações.")
    face_app.prepare(ctx_id=-1, det_size=(320, 320))

# ================= Configurações =================
user_states = {}
user_states_lock = Lock()
MOVE_THRESHOLD = 25
STABLE_SIZE_VARIATION = 0.15
STABLE_FRAMES_REQUIRED = 3
CENTER_TOLERANCE = 0.20
FACE_MATCH_THRESHOLD = 0.65  # <<< LIMIAR DE ACEITAÇÃO DO ROSTO
BATCH_MATCH_RATIO = 0.6      # <<< % de frames que precisam passar para considerar "mesmo rosto"


class FaceLivenessService:

    # ----------------- Similaridade -----------------
    @staticmethod
    def compute_similarity(emb1, emb2):
        if emb1 is None or emb2 is None:
            return 0.0
        sim = float(np.dot(emb1, emb2) / (norm(emb1) * norm(emb2)))
        print(f"[SIMILARITY] Similaridade calculada: {sim:.4f}")
        return sim

    # ----------------- Centralização -----------------
    @staticmethod
    def is_centered(bbox, img_shape):
        x_center = (bbox[0] + bbox[2]) / 2
        y_center = (bbox[1] + bbox[3]) / 2
        dx = abs(x_center - img_shape[1] / 2) / (img_shape[1] / 2)
        dy = abs(y_center - img_shape[0] / 2) / (img_shape[0] / 2)
        centered = dx <= CENTER_TOLERANCE and dy <= CENTER_TOLERANCE
        print(f"[CENTER] dx={dx:.3f}, dy={dy:.3f}, centered={centered}")
        return centered

    # ----------------- Detecção de movimento -----------------
    @staticmethod
    def detect_head_movement(state, curr_bbox):
        prev_bbox = state.get("prev_bbox")
        if prev_bbox is None:
            state["prev_bbox"] = curr_bbox
            state["stable_frames"] = 0
            state["consistent_dir"] = None
            print("[MOVE] Primeiro frame, bbox inicial salva.")
            return None

        dx = ((curr_bbox[0] + curr_bbox[2]) / 2) - ((prev_bbox[0] + prev_bbox[2]) / 2)
        prev_width = prev_bbox[2] - prev_bbox[0]
        curr_width = curr_bbox[2] - curr_bbox[0]
        size_ratio = abs(curr_width - prev_width) / prev_width

        if size_ratio > STABLE_SIZE_VARIATION:
            state["stable_frames"] = 0
            state["consistent_dir"] = None
            state["prev_bbox"] = curr_bbox
            print(f"[MOVE] Variação de tamanho grande ({size_ratio:.2f}), resetando estabilidade.")
            return None

        direction = None
        if dx > MOVE_THRESHOLD:
            direction = "DIREITA"
        elif dx < -MOVE_THRESHOLD:
            direction = "ESQUERDA"

        if direction:
            if direction == state.get("consistent_dir"):
                state["stable_frames"] += 1
            else:
                state["consistent_dir"] = direction
                state["stable_frames"] = 1

            if state["stable_frames"] >= STABLE_FRAMES_REQUIRED:
                print(f"[MOVE] Movimento {direction} confirmado após {state['stable_frames']} frames.")
                state["stable_frames"] = 0
                state["prev_bbox"] = curr_bbox
                return direction

        state["prev_bbox"] = curr_bbox
        return None

    # ----------------- Processa 1 frame -----------------
    @staticmethod
    def process_frame(db: Session, user_id: int, frame_bytes: bytes):
        np_arr = np.frombuffer(frame_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        faces = face_app.get(img)

        if not faces:
            return {"status": "no_face_detected", "message": "Nenhum rosto detectado"}

        curr_face = faces[0]
        curr_bbox = curr_face.bbox.tolist()
        curr_emb = curr_face.embedding.tolist()

        with user_states_lock:
            # === Buscar faces registradas do user ===
            faces_db = db.query(Face).filter(Face.user_id == user_id).all()
            if not faces_db:
                return {"status": "error", "message": "Nenhuma face registrada para este usuário"}

            # Seleciona face mais similar
            best_score = 0.0
            selected_face = faces_db[0]
            for f in faces_db:
                sim = FaceLivenessService.compute_similarity(np.array(f.embedding, dtype=np.float32), curr_emb)
                if sim > best_score:
                    best_score = sim
                    selected_face = f

            # === Verificação de correspondência ===
            same_person = best_score >= FACE_MATCH_THRESHOLD
            match_message = (
                f" Mesmo rosto detectado (similaridade {best_score:.2f})"
                if same_person else
                f" Rosto diferente detectado (similaridade {best_score:.2f})"
            )
            print(f"[MATCH] {match_message}")

            # === Buscar ou criar estado no banco ===
            db_state = db.query(FaceLivenessState).filter_by(user_id=user_id).first()
            if not db_state:
                db_state = FaceLivenessState(
                    face_id=selected_face.face_id,
                    user_id=user_id,
                    movement_history=[],
                    required_sequence=["ESQUERDA", "DIREITA"],
                    next_expected_move="ESQUERDA",
                    finished=False,
                )
                db.add(db_state)
                db.commit()
                db.refresh(db_state)
                print(f"[STATE] Novo estado criado para user_id={user_id}, face_id={selected_face.face_id}")
            else:
                # Atualiza sempre o face_id mais recente
                db_state.face_id = selected_face.face_id
                db.commit()

            # === Controle em memória ===
            state = user_states.get(user_id)
            if not state:
                state = {
                    "movement_history": db_state.movement_history or [],
                    "required_sequence": db_state.required_sequence or ["ESQUERDA", "DIREITA"],
                    "next_expected_move": db_state.next_expected_move or "ESQUERDA",
                    "finished": db_state.finished or False,
                    "prev_bbox": None,
                    "consistent_dir": None,
                    "stable_frames": 0,
                    "last_commit": time.time()
                }
                user_states[user_id] = state

            # === Movimento da cabeça ===
            centered = FaceLivenessService.is_centered(curr_bbox, img.shape)
            move = None
            if not state["finished"] and centered:
                move = FaceLivenessService.detect_head_movement(state, curr_bbox)

            just_finished = False
            if move and move == state["next_expected_move"]:
                state["movement_history"].append(move)
                if len(state["movement_history"]) < len(state["required_sequence"]):
                    state["next_expected_move"] = state["required_sequence"][len(state["movement_history"])]
                else:
                    state["next_expected_move"] = None
                    state["finished"] = True
                    just_finished = True

            # Atualiza banco
            if time.time() - state["last_commit"] > 5 or just_finished:
                db_state.movement_history = state["movement_history"]
                db_state.next_expected_move = state["next_expected_move"]
                db_state.finished = state["finished"]
                db.commit()
                state["last_commit"] = time.time()

        return {
            "status": "ok",
            "data": {
                "movement_history": state["movement_history"],
                "required_sequence": state["required_sequence"],
                "next_expected_move": state["next_expected_move"],
                "finished": state["finished"],
                "just_finished": just_finished,
                "centered": centered,
                "best_similarity": best_score,
                "same_person": same_person,
                "message": match_message,
                "face_id": selected_face.face_id,
            },
        }

    # ----------------- Processa lote de frames com maioria -----------------
    @staticmethod
    def process_batch_frames(db: Session, user_id: int, frame_list: list[bytes]):
        results = []
        similarities = []

        for i, frame_bytes in enumerate(frame_list):
            print(f"[BATCH] Processando frame {i+1}/{len(frame_list)}")
            result = FaceLivenessService.process_frame(db, user_id, frame_bytes)
            results.append(result)
            similarities.append(result["data"]["best_similarity"])

        # --- Decisão por maioria ---
        matching_frames = sum(1 for s in similarities if s >= FACE_MATCH_THRESHOLD)
        match_ratio = matching_frames / len(similarities) if similarities else 0
        same_person_batch = match_ratio >= BATCH_MATCH_RATIO

        batch_message = (
            f" Mesmo rosto na maioria dos frames ({match_ratio*100:.0f}%)"
            if same_person_batch else
            f" Rosto diferente na maioria dos frames ({match_ratio*100:.0f}%)"
        )
        print(f"[BATCH MATCH] {batch_message}")

        return {
            "status": "ok",
            "same_person_batch": same_person_batch,
            "matching_ratio": match_ratio,
            "batch_message": batch_message,
            "data": results[-1]["data"] if results else {},
            "batch_results": results,
        }
