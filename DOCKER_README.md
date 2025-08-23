# 🐳 Docker Инструкции

## 📋 Обзор

Проект использует микросервисную архитектуру с тремя независимыми контейнерами:

1. **main-app** (порт 8000) - Основное веб-приложение
2. **video-converter** (порт 8002) - Сервис конвертации видео в аудио
3. **transcription-service** (порт 8001) - Сервис транскрипции

## 🚀 Быстрый старт

### 1. Проверка системы
```powershell
./scripts/check-docker.ps1
```

### 2. Сборка и запуск всех сервисов
```powershell
./scripts/docker-start-all.ps1
```

### 3. Проверка состояния
```powershell
./scripts/check-docker.ps1
```

### 4. Полная пересборка (если есть проблемы)
```powershell
./scripts/docker-clean-rebuild.ps1
```

## 🔧 Детальные команды

### Сборка образов
```powershell
# Все образы
./scripts/docker-build-microservices.ps1

# Отдельные образы
./scripts/docker-build-main.ps1
./scripts/docker-build-converter.ps1
./scripts/docker-build-transcription.ps1
```

### Запуск сервисов
```powershell
# Все сервисы
./scripts/docker-run-microservices.ps1

# Отдельные сервисы
./scripts/docker-run-main.ps1
./scripts/docker-run-converter.ps1
./scripts/docker-run-transcription.ps1
```

### Остановка
```powershell
./scripts/docker-stop.ps1
```

### Полная очистка и пересборка
```powershell
./scripts/docker-clean-rebuild.ps1
```

## 📊 Мониторинг

### Проверка статуса контейнеров
```powershell
docker ps
```

### Просмотр логов
```powershell
# Все контейнеры
docker-compose -f app/docker/docker-compose.yml logs -f

# Отдельный контейнер
docker logs -f media-processor-main
docker logs -f media-processor-converter
docker logs -f media-processor-transcription
```

### Health checks
```powershell
# Проверка health endpoints
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
```

## 🏗️ Архитектура

### Основное приложение (main-app)
- **Порт**: 8000
- **Зависимости**: Минимальные (FastAPI, uvicorn)
- **Функции**: Веб-интерфейс, координация микросервисов

### Конвертер видео (video-converter)
- **Порт**: 8002
- **Зависимости**: ffmpeg, ffmpeg-python
- **Функции**: Конвертация видео в аудио

### Сервис транскрипции (transcription-service)
- **Порт**: 8001
- **Зависимости**: WhisperX, torch, librosa, ffmpeg
- **Функции**: Транскрипция аудио/видео файлов

## 🔍 Устранение неполадок

### Проблемы с портами
```powershell
# Проверка занятых портов
netstat -an | Select-String ":8000|:8001|:8002"
```

### Проблемы с образами
```powershell
# Удаление старых образов
docker rmi media-processor-main:latest
docker rmi media-processor-converter:latest
docker rmi media-processor-transcription:latest

# Пересборка
./scripts/docker-build-microservices.ps1
```

### Проблемы с контейнерами
```powershell
# Принудительная остановка
docker-compose -f app/docker/docker-compose.yml down --remove-orphans

# Очистка
docker system prune -f
```

### Проблемы с зависимостями
```powershell
# Проверка Docker
docker --version
docker-compose --version

# Перезапуск Docker Desktop
```

## 📁 Структура файлов

```
app/
├── docker/
│   ├── Dockerfile              # Основное приложение
│   ├── docker-compose.yml      # Оркестрация
│   └── requirements.txt        # Зависимости основного приложения
├── features/
│   ├── video_to_audio/
│   │   ├── docker/
│   │   │   ├── Dockerfile      # Конвертер
│   │   │   └── requirements.txt
│   │   └── microservice.py
│   └── transcription/
│       ├── docker/
│       │   ├── Dockerfile      # Транскрипция
│       │   └── requirements.txt
│       └── microservice.py
└── main.py
```

## ⚡ Оптимизация

### Размер образов
- Используются `python:3.11-slim` базовые образы
- Минимальные системные зависимости
- `.dockerignore` исключает ненужные файлы

### Производительность
- Health checks для мониторинга
- Автоматический restart контейнеров
- Изолированные volumes для данных

### Безопасность
- Непривилегированные контейнеры
- Минимальные права доступа
- Изолированная сеть

## 🔄 Обновление

### Обновление кода
```powershell
# Остановка
./scripts/docker-stop.ps1

# Пересборка
./scripts/docker-build-microservices.ps1

# Запуск
./scripts/docker-run-microservices.ps1
```

### Обновление зависимостей
1. Отредактируйте `requirements.txt` файлы
2. Пересоберите образы
3. Перезапустите контейнеры

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `docker logs <container-name>`
2. Проверьте health status: `./scripts/check-docker.ps1`
3. Перезапустите контейнеры: `./scripts/docker-stop.ps1 && ./scripts/docker-run-microservices.ps1`
4. Пересоберите образы: `./scripts/docker-build-microservices.ps1`
