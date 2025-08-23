# Легкий образ для транскрипции
FROM python:3.11-bullseye

# Метаданные
LABEL maintainer="Media Processor Team"
LABEL description="Lightweight transcription service with WhisperX"

# Установка только необходимых системных зависимостей
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    curl \
    elfutils \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копирование только необходимых requirements
COPY app/features/transcription/docker/requirements.txt .

# Установка Python зависимостей с флагами для ctranslate2
ENV CT2_CUDA=0
ENV CT2_CPU_ONLY=1

RUN pip install --no-cache-dir -r requirements.txt

# CPU-версия ctranslate2 не требует execstack

# FastAPI зависимости уже включены в requirements.txt

# Копирование только необходимых файлов
COPY app/core/ ./app/core/
COPY app/features/transcription/ ./app/features/transcription/
COPY app/features/__init__.py ./app/features/
COPY app/__init__.py ./app/

# Создание необходимых директорий
RUN mkdir -p uploads outputs logs

# Настройка переменных окружения для исправления проблем с ctranslate2
ENV LD_LIBRARY_PATH=/usr/local/lib/python3.11/site-packages/ctranslate2
ENV CT2_CUDA=0
ENV CT2_CPU_ONLY=1
ENV PYTHONPATH=/app

# Открытие порта для микросервиса
EXPOSE 8001

# Команда запуска микросервиса транскрипции
CMD ["python", "-m", "app.features.transcription.microservice"]