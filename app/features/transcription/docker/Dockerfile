# GPU образ для транскрипции с CUDA
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

# Метаданные
LABEL maintainer="Media Processor Team"
LABEL description="GPU transcription service with WhisperX and CUDA support"

# Установка Python и системных зависимостей
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    ffmpeg \
    libsndfile1 \
    curl \
    elfutils \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Создание символических ссылок для python
RUN ln -s /usr/bin/python3 /usr/bin/python

# Рабочая директория
WORKDIR /app

# Копирование requirements
COPY app/features/transcription/docker/requirements.txt .

# Установка PyTorch с GPU поддержкой
RUN pip3 install --no-cache-dir \
    torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu121

# Установка остальных зависимостей
RUN pip3 install --no-cache-dir -r requirements.txt

# Копирование файлов приложения
COPY app/core/ ./app/core/
COPY app/features/transcription/ ./app/features/transcription/
COPY app/features/__init__.py ./app/features/
COPY app/__init__.py ./app/

# Создание необходимых директорий для кэширования моделей
RUN mkdir -p \
    /app/app/features/transcription/models_cache \
    /root/.cache/huggingface \
    /root/.cache/whisper \
    uploads \
    outputs \
    logs

# Создание символических ссылок для кэширования
RUN ln -sf /app/app/features/transcription/models_cache /root/.cache/huggingface && \
    ln -sf /app/app/features/transcription/models_cache /root/.cache/whisper

# Настройка переменных окружения для GPU и кэширования моделей
ENV PYTHONPATH=/app
ENV CUDA_VISIBLE_DEVICES=0
ENV HF_HOME=/app/app/features/transcription/models_cache
ENV TRANSFORMERS_CACHE=/app/app/features/transcription/models_cache
ENV WHISPERX_CACHE_DIR=/app/app/features/transcription/models_cache
ENV TORCH_HOME=/app/app/features/transcription/models_cache
ENV HF_DATASETS_CACHE=/app/app/features/transcription/models_cache

# Открытие порта для микросервиса
EXPOSE 8002

# Команда запуска микросервиса транскрипции
CMD ["python3", "-m", "app.features.transcription.microservice"]