#!/bin/bash

echo "🚀 Запуск Ollama Processing Service..."

# Проверяем переменные окружения
export OLLAMA_HOST=${OLLAMA_HOST:-"ollama:11434"}
export PORT=${PORT:-8004}
export HOST=${HOST:-"0.0.0.0"}
export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-"0"}

echo "🔧 Настройки:"
echo "   OLLAMA_HOST: $OLLAMA_HOST"
echo "   PORT: $PORT"
echo "   HOST: $HOST"
echo "   CUDA_VISIBLE_DEVICES: $CUDA_VISIBLE_DEVICES"

# Проверяем GPU доступность
echo "🔍 Проверяем GPU..."
if command -v nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA GPU обнаружен:"
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader,nounits
else
    echo "⚠️  NVIDIA GPU не обнаружен, будет использоваться CPU"
fi

# Проверяем, что Python и необходимые модули доступны
echo "🔍 Проверяем Python окружение..."
python --version
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import torch; print(f'CUDA доступен: {torch.cuda.is_available()}')"
python -c "import torch; print(f'CUDA устройств: {torch.cuda.device_count()}')"
python -c "import torch; print(f'CUDA устройство 0: {torch.cuda.get_device_name(0)}')"
python -c "import ollama; print('Ollama модуль доступен')"
python -c "import fastapi; print('FastAPI доступен')"

# Ждем, пока Ollama сервер запустится
echo "⏳ Ожидание запуска Ollama сервера..."
max_attempts=60
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -s http://$OLLAMA_HOST/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama сервер доступен"
        break
    else
        echo "⏳ Попытка $attempt/$max_attempts: Ollama сервер не доступен, ждем..."
        sleep 5
        attempt=$((attempt + 1))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ Ollama сервер не доступен по адресу http://$OLLAMA_HOST после $max_attempts попыток"
    echo "💡 Проверяем доступность сервера..."
    curl -v http://$OLLAMA_HOST/api/tags || echo "Сервер недоступен"
    exit 1
fi

# Проверяем доступные модели
echo "📦 Проверяем доступные модели..."
models_response=$(curl -s http://$OLLAMA_HOST/api/tags)
if [ $? -eq 0 ]; then
    models=$(echo "$models_response" | jq -r '.models[].name' 2>/dev/null || echo "")
    if [ -n "$models" ]; then
        echo "   Доступные модели:"
        echo "$models" | while read -r model; do
            echo "   - $model"
        done
    else
        echo "   Нет установленных моделей"
    fi
else
    echo "   Не удалось получить список моделей"
fi

# Запускаем микросервис
echo "🚀 Запуск микросервиса Ollama Processing..."
python -m app.features.ollama_processing.microservice
