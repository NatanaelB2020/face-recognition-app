# app/model/face.py
from sqlalchemy import Column, Integer, ForeignKey, String, ARRAY, DateTime, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.data.database import Base
from app.model.user import User

class Face(Base):
    __tablename__ = "faces"

    face_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=True)
    source = Column(String(50), nullable=False, default="UPLOAD")
    embedding = Column(ARRAY(Float), nullable=False)   # embedding principal
    image_data = Column(Text, nullable=False)         # imagem base64
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="faces")
    liveness_states = relationship("FaceLivenessState", back_populates="face", cascade="all, delete-orphan")
