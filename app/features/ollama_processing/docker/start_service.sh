#!/bin/bash

# Функция для корректного завершения
cleanup() {
    echo "🛑 Получен сигнал завершения, останавливаем сервисы..."
    if [ ! -z "$OLLAMA_PID" ]; then
        echo "🛑 Останавливаем Ollama сервер (PID: $OLLAMA_PID)..."
        kill $OLLAMA_PID 2>/dev/null
        wait $OLLAMA_PID 2>/dev/null
    fi
    if [ ! -z "$MICROSERVICE_PID" ]; then
        echo "🛑 Останавливаем микросервис (PID: $MICROSERVICE_PID)..."
        kill $MICROSERVICE_PID 2>/dev/null
        wait $MICROSERVICE_PID 2>/dev/null
    fi
    echo "✅ Все сервисы остановлены"
    exit 0
}

# Устанавливаем обработчики сигналов
trap cleanup SIGTERM SIGINT

echo "🚀 Запуск Ollama Processing Service..."

# Проверяем переменные окружения
export OLLAMA_HOST=${OLLAMA_HOST:-"localhost:11434"}
export PORT=${PORT:-8004}
export HOST=${HOST:-"0.0.0.0"}
export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-"0"}
export OLLAMA_MODELS=${OLLAMA_MODELS:-"/app/app/features/ollama_processing/models_cache"}

echo "🔧 Настройки:"
echo "   OLLAMA_HOST: $OLLAMA_HOST"
echo "   PORT: $PORT"
echo "   HOST: $HOST"
echo "   CUDA_VISIBLE_DEVICES: $CUDA_VISIBLE_DEVICES"
echo "   OLLAMA_MODELS: $OLLAMA_MODELS"

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

# Запускаем Ollama сервер в фоновом режиме
echo "🚀 Запуск Ollama сервера..."
echo "🔍 Проверяем, что ollama доступен..."
which ollama
ollama --version

echo "🚀 Запускаем ollama serve..."
# Убиваем существующие процессы ollama если есть
pkill -f "ollama serve" || true
sleep 2

ollama serve &
OLLAMA_PID=$!
echo "📝 Ollama PID: $OLLAMA_PID"

# Ждем, пока Ollama сервер запустится
echo "⏳ Ожидание запуска Ollama сервера..."
max_attempts=60
attempt=1

while [ $attempt -le $max_attempts ]; do
    # Проверяем, что процесс Ollama все еще жив
    if ! kill -0 $OLLAMA_PID 2>/dev/null; then
        echo "❌ Процесс Ollama (PID: $OLLAMA_PID) завершился неожиданно"
        echo "🔍 Проверяем логи процесса..."
        ps aux | grep ollama
        exit 1
    fi
    
    if curl -s http://$OLLAMA_HOST/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama сервер доступен"
        break
    else
        echo "⏳ Попытка $attempt/$max_attempts: Ollama сервер не доступен, ждем..."
        echo "🔍 Проверяем процессы..."
        ps aux | grep ollama
        sleep 5
        attempt=$((attempt + 1))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ Ollama сервер не доступен по адресу http://$OLLAMA_HOST после $max_attempts попыток"
    echo "💡 Проверяем доступность сервера..."
    curl -v http://$OLLAMA_HOST/api/tags || echo "Сервер недоступен"
    # Убиваем процесс Ollama если он запущен
    if [ ! -z "$OLLAMA_PID" ]; then
        kill $OLLAMA_PID 2>/dev/null
    fi
    exit 1
fi

# Проверяем и создаем директорию для кэширования моделей
echo "📁 Проверяем директорию для кэширования моделей..."
if [ ! -d "$OLLAMA_MODELS" ]; then
    echo "   Создаем директорию: $OLLAMA_MODELS"
    mkdir -p "$OLLAMA_MODELS"
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

# Запускаем микросервис в фоновом режиме
echo "🚀 Запуск микросервиса Ollama Processing..."
python -m app.features.ollama_processing.microservice &
MICROSERVICE_PID=$!

echo "✅ Все сервисы запущены:"
echo "   - Ollama сервер (PID: $OLLAMA_PID)"
echo "   - Микросервис (PID: $MICROSERVICE_PID)"
echo "   - Веб-интерфейс доступен по адресу: http://localhost:$PORT"

# Ждем завершения микросервиса
wait $MICROSERVICE_PID
