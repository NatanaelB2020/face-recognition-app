from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime


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
    source: Literal["UPLOAD", "CAMERA"]  


class FaceResponse(BaseModel):
    id: int
    user_id: int
    filename: Optional[str] = None
    image_base64: Optional[str] = None
    source: str
    created_at: datetime   

    class Config:
        from_attributes = True


# -------------------
# Face Matching / Liveness
# -------------------
class FaceMatchResponse(BaseModel):
    match: bool
    score: Optional[float] = None
    user_id: Optional[int] = None
    face_id: Optional[int] = None
    message: Optional[str] = None
