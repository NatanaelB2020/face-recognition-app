# test_liveness.py
from app.data.database import get_db, Base, engine
from app.model.user import User
from app.model.face import Face

from app.services.face_liveness_service import check_face_liveness_visual

def main():
   
    Base.metadata.create_all(bind=engine)

    db = next(get_db())

    user_id = 1
    face_id = 10

    threshold = 0.8
    movements_required = 2
    frames_to_capture = 60

    print("==> Iniciando teste de liveness. Use a câmera e mova a cabeça!")

    result = check_face_liveness_visual(
    db=db,
    user_id=user_id,
    face_id=face_id,
    threshold=threshold,
    movements_required=movements_required,
    frames_to_capture=frames_to_capture
)

    print("==> Resultado do liveness:")
    print(result)

if __name__ == "__main__":
    main()
