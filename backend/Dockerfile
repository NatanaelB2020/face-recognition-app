FROM python:3.11-slim

WORKDIR /usr/src/app

# Dependências do sistema (psycopg2)
RUN apt-get update && apt-get install -y \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependências
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o código da aplicação
COPY app/ ./app

# Comando para rodar a aplicação (sem --reload para produção)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
