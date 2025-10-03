
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.data.database import get_db
from app.services.face_liveness_service import check_face_liveness_visual


router = APIRouter()

@router.get("/faces/liveness/live")
def face_liveness_live_endpoint(
    user_id: int,
    face_id: int,
    db: Session = Depends(get_db),
    threshold: float = 0.8,
    movements_required: int = 2,
    frames_to_capture: int = 30
):
    """
    Endpoint de liveness ativo em tempo real.
    - Abre a câmera e exibe janela OpenCV
    - Usuário deve mover a cabeça para a esquerda/direita
    - Pressione 'q' para encerrar a captura antes do tempo
    """
    try:
        result = check_face_liveness_visual(
            db=db,
            user_id=user_id,
            face_id=face_id,
            threshold=threshold,
            movements_required=movements_required,
            frames_to_capture=frames_to_capture
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
