# 📘 Face Liveness Detection – Documentação Técnica

Solução corporativa para verificação de vivacidade facial (**liveness detection**) e reconhecimento facial. A aplicação é composta por **Frontend**, **Backend** e **Banco de Dados**, com execução integrada via Docker. O sistema permite:
* Cadastrar usuários.
* Registrar imagens base (embeddings).
* Realizar **liveness ativo**.
* Realizar **autenticação facial**.

A API abre a câmera em tempo real, exibe setas indicando movimentos esperados (esquerda, direita, cima, baixo), detecta variações de **yaw**, **pitch** e **roll** (ângulos da cabeça), compara *embeddings* faciais com a face cadastrada no banco e retorna se o rosto é **real (live)** ou **falso (spoof)**.

---

## 🏗 Arquitetura da Aplicação
A solução segue uma arquitetura de três camadas: **Frontend → Backend → Banco de Dados**.

mermaid
flowchart LR
User((Usuário)) --> FE[Frontend<br>Vite/React]
FE --> BE[Backend<br>FastAPI]
BE --> DB[(PostgreSQL)]
subgraph Infraestrutura
    FE
    BE
    DB
end


*🧠 Tecnologias Utilizadas*
| Camada | Tecnologias Principais |
| --- | --- |
| Backend | FastAPI, SQLAlchemy, Face Recognition / dlib, MediaPipe, OpenCV, NumPy |
| Frontend | Vite, React, Web APIs de câmera |
| Infraestrutura | Docker, Docker Compose, PostgreSQL |

*📂 Estrutura do Projeto (Arquivos Chave)*
A estrutura principal é dividida em `backend/` e `frontend/`.

- Arquivos de Orquestração Docker:
    - `docker-compose.db.yml` (PostgreSQL)
    - `docker-compose-backend.yml` (FastAPI)
    - `docker-compose-frontend.yml` (React)
- Cada arquivo é totalmente independente, permitindo subir módulos separados.

Módulos Chave do Backend (`backend/app/`):
- `data/database.py`: Criação automática das tabelas.
- `services/face_liveness_service.py`: Lógica central de detecção de vivacidade.
- `services/face_service.py`: Busca de faces e embeddings.
- `services/capture_image.py`: Comparação facial.
- `routes/face_liveness_router.py`: Endpoint `/faces/liveness/live`.

*⚙ Como Subir a Aplicação*
*Inicialização (Comandos de Exemplo)*
- Banco de Dados (na pasta `backend/`):

bash
docker compose -f docker-compose.db.yml up -d

- Backend API (na pasta `backend/`):

bash
docker compose -f docker-compose-backend.yml up -d

- Frontend Web (na pasta `frontend/`):

bash
docker compose -f docker-compose-frontend.yml up -d


*URLs de Acesso*
| Serviço | URL |
| --- | --- |
| API Principal (Backend) | http://localhost:8000 |
| Documentação (Swagger) | http://localhost:8000/docs |
| Aplicação Web (Frontend) | http://localhost:5173 |

*💡 Criação Automática das Tabelas*
O módulo `backend/app/data/database.py` cria todas as tabelas automaticamente. Nenhuma preparação manual do banco é necessária.

*▶ Endpoint Principal – Liveness Detection*
`GET /faces/liveness/live`

| Parâmetro | Tipo | Padrão | Descrição |
| --- | --- | --- | --- |
| `user_id` | int | - | ID do usuário dono da face (obrigatório) |
| `face_id` | int | - | ID da face cadastrada (obrigatório) |
| `threshold` | float | 0.8 | Limite mínimo de similaridade facial |
| `movements_required` | int | 2 | Movimentos mínimos para validar liveness |
| `frames_to_capture` | int | 30 | Número de frames a capturar da câmera |

Exemplo de Requisição:

bash
curl "http://127.0.0.1:8000/faces/liveness/live?user_id=1&face_id=2"


Exemplo de Retorno:

{
  "match": true,
  "score": 0.89,
  "user_id": 1,
  "face_id": 2,
  "message": "Liveness confirmado (4/2 movimentos detectados)"
}


*🎥 Demonstração e Uso*
- Durante a execução, uma janela OpenCV será aberta mostrando a câmera.
- Mova a cabeça para os lados e para cima/baixo conforme as setas.
- Pressione `q` para encerrar a captura manualmente.

*⚠ Passo Obrigatório Antes do Liveness*
Para permitir o cadastro das imagens base (embeddings) via frontend, é necessário criar um usuário utilizando o Swagger:
- Acesse: http://localhost:8000/docs
- Utilize o endpoint: `POST /users`

Após a criação do usuário, o fluxo de cadastro de face, captura e liveness será realizado pelo frontend de forma automática.

*📦 Requisitos e Dependências*
- Requisitos Mínimos:
    - Python 3.8+
    - Webcam funcionando
    - CMake instalado (necessário para compilar dlib, se aplicável)
- Dependências Principais:
    - `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `opencv-python`, `numpy`, `cmake`, `dlib`, `face-recognition`, `mediapipe`

*🧑‍💻 Desenvolvedor Responsável*
Natanael Amaral de Barros
- GitHub: https://github.com/NatanaelB2020
- LinkedIn: https://www.linkedin.com/in/natanael-amaral-9154ab175/

```
