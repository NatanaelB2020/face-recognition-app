from pydantic import BaseModel

class FaceCreate(BaseModel):
    user_id: int
    image_data: bytes  # você vai enviar a imagem como base64

class FaceResponse(FaceCreate):
    id: int

    class Config:
        orm_mode = True
