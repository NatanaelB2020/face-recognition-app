# app/routes/face.py
from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.data.database import get_db
from app.model.face import Face
from app.schema.schemas import FaceResponse
from app.services.face_service import get_face_by_id, save_face
from app.services.capture_image import capture_image

router = APIRouter()

@router.post("/faces/", response_model=FaceResponse)
def upload_face(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_data = file.file.read()
    return save_face(
        db=db,
        user_id=user_id,
        file_data=file_data,
        filename=file.filename,
        source="UPLOAD"
    )

@router.get("/faces/raw/{user_id}/{face_id}")
def retrieve_face_raw(user_id: int, face_id: int, db: Session = Depends(get_db)):
    db_face = db.query(Face).filter(Face.user_id == user_id, Face.id == face_id).first()
    if not db_face:
        raise HTTPException(status_code=404, detail="Face not found")

    return StreamingResponse(BytesIO(db_face.image_data), media_type="image/jpeg")

@router.get("/capture")
def capture():
    """
    Captura uma imagem da câmera e retorna em JPEG (sem salvar).
    """
    try:
        image_bytes = capture_image()
        return Response(content=image_bytes, media_type="image/jpeg")
    except Exception as e:
        return {"error": str(e)}

@router.post("/capture/save", response_model=FaceResponse)
def capture_and_save(user_id: int, db: Session = Depends(get_db)):
    """
    Captura uma imagem da câmera e salva no banco.
    """
    try:
        image_bytes = capture_image()
        return save_face(
            db=db,
            user_id=user_id,
            file_data=image_bytes,
            filename="captured.jpg",
            source="CAMERA"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
