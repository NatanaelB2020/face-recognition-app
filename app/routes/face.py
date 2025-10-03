# app/routes/face.py
from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
import base64
import cv2

from app.data.database import get_db
from app.model.face import Face
from app.schema.schemas import FaceResponse, FaceMatchResponse
from app.services.face_service import get_face_by_id, save_face, extract_embedding
from app.services.capture_image import capture_image, find_matching_face

router = APIRouter()


@router.post("/faces/", response_model=FaceResponse)
def upload_face(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        file_data = file.file.read()
        face_response = save_face(
            db=db,
            user_id=user_id,
            file_data=file_data,
            filename=file.filename,
            source="UPLOAD"
        )
        return face_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/faces/raw/{user_id}/{face_id}")
def retrieve_face_raw(user_id: int, face_id: int, db: Session = Depends(get_db)):
    try:
        db_face = db.query(Face).filter(Face.user_id == user_id, Face.id == face_id).first()
        if not db_face:
            raise HTTPException(status_code=404, detail="Face not found")
        image_bytes = base64.b64decode(db_face.image_data)
        return StreamingResponse(BytesIO(image_bytes), media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capture")
def capture():
    try:
        rgb_frame = capture_image()
        bgr_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
        ret, buffer = cv2.imencode(".jpg", bgr_frame)
        if not ret:
            raise RuntimeError("Falha ao converter imagem para JPEG")
        return Response(content=buffer.tobytes(), media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/capture/save", response_model=FaceResponse)
def capture_and_save(user_id: int, db: Session = Depends(get_db)):
    try:
        rgb_frame = capture_image()
        face_response = save_face(
            db=db,
            user_id=user_id,
            img_rgb=rgb_frame,
            filename=f"captured_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jpg",
            source="CAMERA"
        )
        return face_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/faces/verify/{user_id}/{face_id}", response_model=FaceMatchResponse)
def verify_face(user_id: int, face_id: int, db: Session = Depends(get_db)):
    """
    Captura uma imagem da webcam e compara com o embedding da face salva.
    Retorna se é match e o score da comparação.
    """
    try:
        # Captura imagem da webcam
        frame_rgb = capture_image()

        # Extrai embedding da imagem capturada
        embedding = extract_embedding(frame_rgb)
        if embedding is None:
            raise HTTPException(status_code=400, detail="Nenhum rosto detectado na captura.")

        # Compara embedding com o embedding salvo no banco
        result = find_matching_face(db, user_id, face_id, embedding)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
