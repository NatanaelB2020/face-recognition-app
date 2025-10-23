# app/model/user.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.data.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)

    faces = relationship("Face", back_populates="user", cascade="all, delete-orphan")
