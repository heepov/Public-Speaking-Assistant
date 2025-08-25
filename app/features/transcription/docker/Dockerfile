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

# Создание необходимых директорий
RUN mkdir -p uploads outputs logs

# Настройка переменных окружения для GPU
ENV PYTHONPATH=/app
ENV CUDA_VISIBLE_DEVICES=0

# Открытие порта для микросервиса
EXPOSE 8001

# Команда запуска микросервиса транскрипции
CMD ["python3", "-m", "app.features.transcription.microservice"]