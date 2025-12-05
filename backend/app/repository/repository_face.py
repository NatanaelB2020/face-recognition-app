from sqlalchemy.orm import Session
from app.model.face import Face

def get_embeddings_by_user(db: Session, user_id: int):
    return (
        db.query(Face.embedding)
        .filter(Face.user_id == user_id)
        .yield_per(1000)
        .all()
    )

def save_face(db: Session, face: Face):
    db.add(face)
