# app/schema/schemas.py
from pydantic import BaseModel
from typing import Optional

# -------------------
# User Schemas
# -------------------
class UserCreate(BaseModel):
    name: str
    email: str


class UserResponse(UserCreate):
    id: int

    class Config:
        from_attributes = True  # pydantic v2 (substitui orm_mode)


# -------------------
# Face Schemas
# -------------------
class FaceCreate(BaseModel):
    user_id: int
    filename: Optional[str] = None
    source: str  # 🔹 "UPLOAD" ou "CAMERA"


class FaceResponse(BaseModel):
    id: int
    user_id: int
    filename: Optional[str] = None
    image_base64: Optional[str] = None  
    source: str  

    class Config:
        from_attributes = True
