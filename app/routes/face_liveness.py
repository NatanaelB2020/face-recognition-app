# app/routes/face_liveness.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.data.database import get_db
from app.services.face_liveness_service import check_face_liveness
from app.services.face_service import load_image_from_bytes
from typing import Optional

router = APIRouter()

@router.post("/faces/liveness")
def face_liveness_endpoint(
    user_id: int,
    face_id: int,
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    threshold: float = 0.8
):
    """
    Endpoint de liveness + reconhecimento facial.
    """
    try:
        img_rgb = None
        if file:
            img_rgb = load_image_from_bytes(file.file.read())

        result = check_face_liveness(
            db=db,
            user_id=user_id,
            face_id=face_id,
            img_rgb=img_rgb,
            threshold=threshold
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
