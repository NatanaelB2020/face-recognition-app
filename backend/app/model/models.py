from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from app.data.database import engine

# Declarative Base
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
