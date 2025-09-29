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


class FaceResponse(BaseModel):
    id: int
    user_id: int
    filename: Optional[str] = None
    image_base64: Optional[str] = None  # usado só na resposta

    class Config:
        from_attributes = True
