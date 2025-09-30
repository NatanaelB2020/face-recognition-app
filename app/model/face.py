# app/model/face.py
from sqlalchemy import Column, Integer, ForeignKey, String, LargeBinary
from sqlalchemy.orm import relationship
from app.data.database import Base

class Face(Base):
    __tablename__ = "faces"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    image_data = Column(LargeBinary, nullable=False)
    filename = Column(String(255), nullable=True)
    source = Column(String(50), nullable=False)  # 🔹 UPLOAD ou CAMERA

    # relacionamento de volta para o usuário
    user = relationship("User", back_populates="faces")
