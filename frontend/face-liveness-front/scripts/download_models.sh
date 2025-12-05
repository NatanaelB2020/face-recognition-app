#!/bin/sh
set -e

MODEL_DIR="/app/public/models"
mkdir -p "$MODEL_DIR"

echo ">> Criando pasta de modelos em: $MODEL_DIR"
echo ">> Baixando modelos tiny-face-detector..."

curl -L -o "$MODEL_DIR/tiny_face_detector_model-weights_manifest.json" \
  https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/tiny_face_detector_model-weights_manifest.json

curl -L -o "$MODEL_DIR/tiny_face_detector_model-shard1" \
  https://github.com/justadudewhohacks/face-api.js/raw/master/weights/tiny_face_detector_model-shard1

echo ">> Modelos baixados!"
