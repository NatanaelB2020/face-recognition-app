# app/routes/face.py
from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.data.database import get_db
from app.model.face import Face
from app.schema.schemas import FaceResponse
from app.services.face_service import get_face_by_id, save_face

router = APIRouter()

@router.post("/faces/", response_model=FaceResponse)
def upload_face(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_data = file.file.read()
    return save_face(db=db, user_id=user_id, file_data=file_data, filename=file.filename)


@router.get("/faces/raw/{user_id}/{face_id}")
def retrieve_face_raw(user_id: int, face_id: int, db: Session = Depends(get_db)):
    db_face = db.query(Face).filter(Face.user_id == user_id, Face.id == face_id).first()
    if not db_face:
        raise HTTPException(status_code=404, detail="Face not found")

    # Retorna a imagem diretamente
    return StreamingResponse(BytesIO(db_face.image_data), media_type="image/jpeg")