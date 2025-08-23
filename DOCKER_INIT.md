# 🐳 Инициализация Docker

## 🚀 Быстрый запуск (одной кнопкой)

```bash
# Собрать и запустить все контейнеры
./scripts/docker-start-all.ps1
```

## 📋 Детальное управление

### Сборка образов
```bash
# Собрать все образы
./scripts/docker-build-microservices.ps1

# Или по отдельности:
./scripts/docker-build-main.ps1        # Основное приложение
./scripts/docker-build-converter.ps1   # Конвертер
./scripts/docker-build-transcription.ps1 # Транскрипция
```

### Запуск контейнеров
```bash
# Запустить все контейнеры
./scripts/docker-run-microservices.ps1

# Или по отдельности:
./scripts/docker-run-main.ps1          # Основное приложение
./scripts/docker-run-converter.ps1     # Конвертер
./scripts/docker-run-transcription.ps1 # Транскрипция
```

### Остановка
```bash
./scripts/docker-stop.ps1
```

### Проверка системы
```bash
./scripts/check-docker.ps1
```

## Структура контейнеров

- **Основной контейнер**: FastAPI + веб-интерфейс
- **Фича 1**: Конвертация видео в аудио
- **Фича 2**: Транскрипция через WhisperX

## Переменные окружения

```bash
HOST=127.0.0.1
PORT=8000
LOG_LEVEL=INFO
DOCKER_ENV=true
```
