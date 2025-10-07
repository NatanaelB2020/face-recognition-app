# 👁️ Face Liveness Detection API  
Verificação de vivacidade facial em tempo real usando **FastAPI**, **OpenCV**, **MediaPipe** e **Face Recognition**.

---

## 🚀 Descrição

Este projeto implementa um **sistema de liveness ativo**, que detecta se uma face é real (viva) por meio de movimentos sutis da cabeça capturados pela câmera.  
É ideal para sistemas de autenticação facial, antifraude e verificação biométrica.

A API expõe um endpoint que:
- Abre a câmera do usuário em tempo real;
- Exibe setas indicando movimentos esperados (esquerda, direita, cima, baixo);
- Detecta variações de yaw, pitch e roll (ângulos da cabeça);
- Compara embeddings faciais com a face cadastrada no banco;
- Retorna se o rosto é **real (live)** ou **falso (spoof)**.

---

## 🧠 Tecnologias Utilizadas

| Tecnologia | Função |
|-------------|--------|
| **FastAPI** | Framework para criação da API REST |
| **SQLAlchemy** | ORM para comunicação com banco de dados |
| **OpenCV** | Captura e exibição de vídeo em tempo real |
| **MediaPipe** | Detecção dos pontos faciais e estimativa de pose |
| **Face Recognition / dlib** | Extração de embeddings e comparação facial |
| **NumPy** | Processamento de vetores numéricos |
| **Uvicorn** | Servidor ASGI para rodar a API |

---

## 📂 Estrutura do Projeto

```
app/
 ├── data/
 │   └── database.py        # Configuração da conexão com o banco
 ├── services/
 │   ├── face_liveness_service.py  # Lógica de detecção de liveness
 │   ├── face_service.py           # Busca de face e embeddings
 │   └── capture_image.py          # Comparação facial
 └── routes/
     └── face_liveness_router.py   # Endpoint /faces/liveness/live
```

---

## ⚙️ Instalação

1. **Clone o repositório**
   ```bash
   git clone https://github.com/NatanaelB2020/face-recognition-app.git
   cd face-liveness-api
   ```

2. **Crie um ambiente virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate     # Linux/Mac
   venv\Scripts\activate        # Windows
   ```

3. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as variáveis de ambiente**
   Crie um arquivo `.env` com suas credenciais:
   ```
   DATABASE_URL=postgresql://usuario:senha@localhost:5432/nome_do_banco
   ```

---

## ▶️ Executando o Projeto

Inicie o servidor com:

```bash
uvicorn app.routes.face_liveness_router:router --reload
```

O servidor estará disponível em:
```
http://127.0.0.1:8000
```

---

## 🧩 Endpoint

### `GET /faces/liveness/live`

#### Parâmetros:
| Nome | Tipo | Padrão | Descrição |
|------|------|---------|------------|
| `user_id` | int | - | ID do usuário dono da face |
| `face_id` | int | - | ID da face cadastrada |
| `threshold` | float | 0.8 | Limite mínimo de similaridade facial |
| `movements_required` | int | 2 | Movimentos mínimos para validar liveness |
| `frames_to_capture` | int | 30 | Número de frames a capturar da câmera |

#### Exemplo de Requisição:
```bash
curl "http://127.0.0.1:8000/faces/liveness/live?user_id=1&face_id=2"
```

#### Exemplo de Retorno:
```json
{
  "match": true,
  "score": 0.89,
  "user_id": 1,
  "face_id": 2,
  "message": "Liveness confirmado (4/2 movimentos detectados)"
}
```

---

## 🎥 Demonstração

Durante a execução:
- Uma janela OpenCV será aberta mostrando a câmera.
- Mova a cabeça para os lados e para cima/baixo.
- Pressione **`q`** para encerrar a captura manualmente.

---

## ⚠️ Requisitos

- Python 3.8+
- Webcam funcionando
- CMake instalado (para compilar `dlib`, se necessário)

---

## 📦 Dependências Principais

```text
fastapi
uvicorn[standard]
sqlalchemy
psycopg2-binary
python-dotenv
python-multipart
opencv-python
opencv-python-headless
numpy
cmake
dlib
face-recognition
mediapipe
```

---

## 💡 Melhorias Futuras

- [ ] Suporte a múltiplos rostos na mesma captura  
- [ ] Integração com reconhecimento facial automático (sem ID manual)  
- [ ] Adição de logs estruturados e métricas de performance  
- [ ] Deploy em Docker com GPU para aceleração via CUDA  

---

## 🧑‍💻 Autor

**Natanael Amaral de Barros**  
📧 https://www.linkedin.com/in/natanael-amaral-9154ab175/
💻 https://github.com/NatanaelB2020



