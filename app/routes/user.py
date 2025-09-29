from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.model.user import User
from app.schema.user import UserCreate, UserResponse
from app.data.database import get_db

router = APIRouter()

@router.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(name=user.name, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
