# Легкий образ для основного приложения
FROM python:3.11-slim

# Метаданные
LABEL maintainer="Media Processor Team"
LABEL description="Lightweight main application server"

# Установка только минимальных системных зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Рабочая директория
WORKDIR /app

# Копирование файлов зависимостей
COPY app/docker/requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Создание необходимых директорий
RUN mkdir -p uploads outputs logs

# Настройка Python path для корректного импорта модулей
ENV PYTHONPATH=/app

# Открытие порта
EXPOSE 8000

# Команда запуска
CMD ["python", "app/main.py"]
