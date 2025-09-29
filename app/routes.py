from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.model import models
from app.schema import schemas
from app.data import database


router = APIRouter()

@router.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = models.User(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
