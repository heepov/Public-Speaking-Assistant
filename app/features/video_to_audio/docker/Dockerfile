# Легкий образ для конвертации видео в аудио
FROM python:3.11-slim

# Метаданные
LABEL maintainer="Media Processor Team"
LABEL description="Lightweight video to audio converter"

# Установка только необходимых системных зависимостей
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копирование только необходимых requirements
COPY app/features/video_to_audio/docker/requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# FastAPI зависимости уже включены в requirements.txt

# Копирование только необходимых файлов
COPY app/core/ ./app/core/
COPY app/features/video_to_audio/ ./app/features/video_to_audio/
COPY app/features/__init__.py ./app/features/
COPY app/__init__.py ./app/

# Создание необходимых директорий
RUN mkdir -p uploads outputs logs

# Настройка Python path для корректного импорта модулей
ENV PYTHONPATH=/app

# Открытие порта для микросервиса
EXPOSE 8002

# Команда запуска микросервиса конвертации
CMD ["python", "-m", "app.features.video_to_audio.microservice"]
