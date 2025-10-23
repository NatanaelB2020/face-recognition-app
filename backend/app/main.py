from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.data.database import engine, Base
from app.routes.user import router as user_router
from app.routes import face_routes

app = FastAPI(
    title="Face Recognition API",
    description="API para gerenciamento de usuários e reconhecimento facial com InsightFace",
    version="1.0.0"
)

# Criar tabelas no banco
Base.metadata.create_all(bind=engine)

# Configuração de CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas
app.include_router(user_router, prefix="/users", tags=["Usuários"])
app.include_router(face_routes.router, prefix="/faces", tags=["Faces"])

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "API de reconhecimento facial está online e funcional!"}
