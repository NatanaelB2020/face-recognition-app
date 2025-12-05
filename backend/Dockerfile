# ===========================================================
# Imagem base Python slim (leve, rápida e suficiente)
# ===========================================================
FROM python:3.11-slim

LABEL maintainer="Natanael Amaral de Barros"

# Evita criação de .pyc e força stdout imediato
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Diretório principal da aplicação
WORKDIR /app

# ===========================================================
# Dependências do sistema (OpenCV + InsightFace)
# ===========================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    curl \
    ca-certificates \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libjpeg-dev \
    libpng-dev \
    libopenblas-dev \
    liblapack-dev \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# ===========================================================
# Copia o arquivo de dependências
# ===========================================================
COPY app/requirements.txt /app/requirements.txt

# ===========================================================
# Instala as dependências Python
# ===========================================================
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir "uvicorn[standard]" \
    && pip install --no-cache-dir -r /app/requirements.txt

# ===========================================================
# Copia toda a aplicação
# ===========================================================
COPY . /app

# ===========================================================
# Cria usuário seguro (não root)
# ===========================================================
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

# Porta exposta da API
EXPOSE 8000

# ===========================================================
# Comando padrão: roda FastAPI com uvicorn
# ===========================================================
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
