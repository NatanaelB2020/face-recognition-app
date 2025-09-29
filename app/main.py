from fastapi import FastAPI
from app.data.database import engine, Base
from app.model.user import User
from app.model.face import Face
from app.routes.user import router as user_router
from app.routes.face import router as face_router

app = FastAPI()

# Criar tabelas
Base.metadata.create_all(bind=engine)

# Incluir rotas
app.include_router(user_router)
app.include_router(face_router)
