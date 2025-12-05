# =============================
# FRONTEND DEV SERVER EM CONTAINER
# =============================
FROM node:20-slim

WORKDIR /app

ENV TZ=America/Sao_Paulo
ENV HOST=0.0.0.0

RUN apt-get update && apt-get install -y curl bash && rm -rf /var/lib/apt/lists/*

COPY package*.json ./
RUN rm -rf node_modules
RUN npm install

COPY . .

RUN chmod +x scripts/download_models.sh && ./scripts/download_models.sh

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
