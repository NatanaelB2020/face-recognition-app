from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.data.database import get_db
from app.services.face_capture_service import save_multiple_faces_from_upload
from app.services.face_liveness_service import FaceLivenessService

router = APIRouter(tags=["Faces"])


@router.post("/upload/{user_id}")
async def upload_faces(
    user_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    if not files:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado.")

    try:
        results = await save_multiple_faces_from_upload(db, user_id, files)
        db.commit()  # único commit
        return {
            "status": "ok",
            "saved_faces": len([r for r in results if r["status"] == "ok"]),
            "details": results
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/liveness/{user_id}")
async def liveness(
    user_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    if not files:
        raise HTTPException(status_code=400, detail="Nenhum frame enviado.")

    try:
        # streaming de frames → sem estourar RAM
        frame_bytes_list = []
        for f in files:
            frame_bytes_list.append(await f.read())

        result = FaceLivenessService.process_batch_frames(
            db=db,
            user_id=user_id,
            frames=frame_bytes_list
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
