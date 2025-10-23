from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.data.database import get_db
from app.services.face_capture_service import save_multiple_faces_from_upload
from app.services.face_verify_service import verify_face_match
from app.services.face_liveness_service import FaceLivenessService
from app.model.face import Face

router = APIRouter(tags=["Faces"])

@router.post("/upload/{user_id}")
async def upload_faces(user_id: int, files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    file_bytes_list = [await file.read() for file in files]
    filenames = [file.filename for file in files]
    results = save_multiple_faces_from_upload(db, user_id, file_bytes_list, filenames, source="UPLOAD")
    return {"status": "ok", "saved_faces": len(results)}

@router.post("/liveness/{user_id}")
async def liveness(user_id: int, files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    try:
        frame_bytes_list = [await file.read() for file in files]
        result = FaceLivenessService.process_batch_frames(db, user_id, frame_bytes_list)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}

