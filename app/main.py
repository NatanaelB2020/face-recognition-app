# app/main.py
from fastapi import FastAPI
from app.data.database import engine, Base
from app.routes.user import router as user_router
from app.routes.face import router as face_router
from app.routes.face_liveness_active import router as face_liveness_active_router

app = FastAPI(
    title="Face Recognition API",
    description="API para gerenciamento de usuários e reconhecimento facial com MediaPipe",
    version="1.0.0"
)

# Criar tabelas no banco
Base.metadata.create_all(bind=engine)

# Incluir rotas com prefixos e tags
app.include_router(user_router, prefix="/users", tags=["Usuários"])
app.include_router(face_router, prefix="/faces", tags=["Faces"])
app.include_router(face_liveness_active_router, prefix="/faces", tags=["Faces Ativas"])  

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "API de reconhecimento facial está online"}
