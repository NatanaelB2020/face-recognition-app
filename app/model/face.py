from sqlalchemy import Column, Integer, ForeignKey, String, ARRAY, DateTime, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.data.database import Base
from app.model.user import User  

class Face(Base):
    __tablename__ = "faces"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # agora armazenamos imagem em base64 (texto)
    image_data = Column(Text, nullable=False)  

    filename = Column(String(255), nullable=True)
    source = Column(String(50), nullable=False, default="UPLOAD")
    created_at = Column(DateTime, default=datetime.utcnow)

    # embedding do rosto (vetor de floats)
    embedding = Column(ARRAY(Float), nullable=True)

    user = relationship("User", back_populates="faces")
