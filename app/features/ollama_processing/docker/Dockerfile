# GPU образ для Ollama Processing с CUDA
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

# Метаданные
LABEL maintainer="Media Processor Team"
LABEL description="GPU ollama processing service with CUDA support"

# Установка Python и системных зависимостей
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    curl \
    wget \
    git \
    jq \
    build-essential \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Создание символических ссылок для python
RUN ln -s /usr/bin/python3 /usr/bin/python

# Устанавливаем Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Проверяем установку Ollama
RUN ollama --version

# Рабочая директория
WORKDIR /app

# Копирование requirements
COPY app/features/ollama_processing/docker/requirements.txt .

# Установка PyTorch с GPU поддержкой
RUN pip3 install --no-cache-dir \
    torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu121

# Установка остальных зависимостей
RUN pip3 install --no-cache-dir -r requirements.txt

# Копирование файлов приложения
COPY app/core/ ./app/core/
COPY app/features/ollama_processing/ ./app/features/ollama_processing/
COPY app/features/__init__.py ./app/features/
COPY app/__init__.py ./app/

# Создание необходимых директорий для кэширования моделей
RUN mkdir -p \
    /app/app/features/ollama_processing/models_cache \
    /root/.ollama \
    uploads \
    outputs \
    logs

# Создание символических ссылок для кэширования
RUN ln -sf /app/app/features/ollama_processing/models_cache /root/.ollama

# Устанавливаем правильные права доступа
RUN chmod -R 755 /root/.ollama
RUN chmod -R 755 /app/app/features/ollama_processing/models_cache

# Настройка переменных окружения для GPU и кэширования моделей
ENV PYTHONPATH=/app
ENV CUDA_VISIBLE_DEVICES=0
ENV OLLAMA_HOST=localhost:11434
ENV PORT=8004
ENV HOST=0.0.0.0
ENV OLLAMA_ORIGINS=*
ENV OLLAMA_MODELS=/app/app/features/ollama_processing/models_cache

# Открытие порта для микросервиса
EXPOSE 8004

# Преобразуем окончания строк и делаем скрипт запуска исполняемым
RUN dos2unix /app/app/features/ollama_processing/docker/start_service.sh
RUN chmod +x /app/app/features/ollama_processing/docker/start_service.sh

# Команда запуска микросервиса
CMD ["/app/app/features/ollama_processing/docker/start_service.sh"]
