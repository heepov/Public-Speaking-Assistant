# GPU образ для Ollama Processing с CUDA
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

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
    && rm -rf /var/lib/apt/lists/*

# Создание символических ссылок для python
RUN ln -s /usr/bin/python3 /usr/bin/python

# Устанавливаем Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
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

# Создание необходимых директорий
RUN mkdir -p uploads outputs logs

# Настройка переменных окружения для GPU
ENV PYTHONPATH=/app
ENV OLLAMA_HOST=localhost:11434
ENV PORT=8004
ENV HOST=0.0.0.0
ENV CUDA_VISIBLE_DEVICES=0
ENV OLLAMA_ORIGINS=*

# Открытие порта для микросервиса
EXPOSE 8004

# Делаем скрипт запуска исполняемым
RUN chmod +x /app/app/features/ollama_processing/docker/start_service.sh

# Команда запуска микросервиса
CMD ["/app/app/features/ollama_processing/docker/start_service.sh"]
