# app/services/face_service.py
import base64
from sqlalchemy.orm import Session
from app.model.face import Face
from app.schema.schemas import FaceResponse

def save_face(db: Session, user_id: int, file_data: bytes, filename: str, source: str) -> FaceResponse:
    db_face = Face(
        user_id=user_id,
        image_data=file_data,
        filename=filename,
        source=source
    )
    db.add(db_face)
    db.commit()
    db.refresh(db_face)

    image_base64 = base64.b64encode(db_face.image_data).decode("utf-8")
    return FaceResponse(
        id=db_face.id,
        user_id=db_face.user_id,
        filename=db_face.filename,
        image_base64=image_base64,
        source=db_face.source
    )

def get_face_by_id(db: Session, user_id: int, face_id: int) -> FaceResponse | None:
    db_face = db.query(Face).filter(Face.user_id == user_id, Face.id == face_id).first()
    if not db_face:
        return None

    image_base64 = base64.b64encode(db_face.image_data).decode("utf-8")
    return FaceResponse(
        id=db_face.id,
        user_id=db_face.user_id,
        filename=db_face.filename,
        image_base64=image_base64,
        source=db_face.source
    )
