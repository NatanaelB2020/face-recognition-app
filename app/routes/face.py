# app/routes/face.py
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.data.database import get_db
from app.schema.schemas import FaceResponse
from app.services.face_service import save_face

router = APIRouter()

@router.post("/faces/", response_model=FaceResponse)
def upload_face(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_data = file.file.read()
    return save_face(db=db, user_id=user_id, file_data=file_data, filename=file.filename)
