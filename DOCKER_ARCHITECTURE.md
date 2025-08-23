# 🐳 Docker Architecture Documentation

## 📋 Обзор архитектуры

Проект построен на микросервисной архитектуре с использованием Docker. Каждый сервис работает независимо и может быть запущен, остановлен или перезапущен без влияния на другие сервисы.

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   main-app      │    │  video-converter │    │transcription-    │
│   (порт 8000)   │    │  (порт 8002)     │    │service (порт 8001)│
│                 │    │                  │    │                  │
│ ✅ Health check │    │ ✅ Health check  │    │ ✅ Health check  │
│ ✅ Легкий образ │    │ ✅ Независимый   │    │ ✅ Независимый   │
│ ✅ Минимальные  │    │ ✅ ffmpeg        │    │ ✅ WhisperX      │
│    зависимости  │    │ ✅ Конвертация   │    │ ✅ Транскрипция  │
└─────────────────┘    └──────────────────┘    └──────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │    Docker Network         │
                    │   (media-network)         │
                    └───────────────────────────┘
```

## 🏗️ Компоненты системы

### 1. **main-app** (Порт 8000)
- **Назначение**: Основной веб-интерфейс и оркестратор
- **Технологии**: FastAPI, Uvicorn, Jinja2, httpx
- **Особенности**: 
  - Легкий образ с минимальными зависимостями
  - Веб-интерфейс для загрузки файлов
  - Оркестрация между микросервисами через HTTP
  - Health checks для мониторинга
  - Асинхронные HTTP-клиенты для взаимодействия с микросервисами

### 2. **video-converter** (Порт 8002)
- **Назначение**: Конвертация видео в аудио
- **Технологии**: FastAPI, ffmpeg-python, ffmpeg, httpx
- **Особенности**:
  - Независимый микросервис
  - Поддержка множества видео форматов
  - Оптимизированный для обработки видео
  - Минимальные зависимости (только ffmpeg + FastAPI)

### 3. **transcription-service** (Порт 8001)
- **Назначение**: Транскрипция аудио/видео файлов
- **Технологии**: FastAPI, WhisperX, PyTorch, torchaudio, librosa
- **Особенности**:
  - Независимый микросервис
  - Поддержка множества языков
  - Кэширование моделей Whisper
  - Тяжелые ML-зависимости изолированы

## 🔧 Технические характеристики

### Сетевая архитектура
- **Сеть**: `media-network` (bridge)
- **Изоляция**: Каждый сервис в отдельном контейнере
- **Коммуникация**: HTTP REST API между сервисами
- **HTTP-клиенты**: httpx для асинхронных запросов

### Volumes и хранение
- **uploads/**: Общая директория для загруженных файлов
- **outputs/**: Общая директория для результатов
- **logs/**: Общая директория для логов
- **whisper-models/**: Кэш моделей Whisper (только для transcription)

### Health Checks
Все сервисы имеют настроенные health checks:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:PORT/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 30-60s
```

## 🚀 Преимущества архитектуры

### ✅ Независимость сервисов
- Каждый сервис может быть запущен независимо
- Отказ одного сервиса не влияет на другие
- Возможность масштабирования отдельных сервисов

### ✅ Легкие образы
- Минимальные зависимости для каждого сервиса
- Оптимизированные Dockerfile'ы
- Быстрая сборка и развертывание

### ✅ Отказоустойчивость
- Health checks для мониторинга
- Автоматический перезапуск контейнеров
- Graceful degradation при недоступности сервисов

### ✅ Масштабируемость
- Горизонтальное масштабирование микросервисов
- Балансировка нагрузки
- Изоляция ресурсов

## 📁 Структура файлов

```
app/
├── core/                    # Общие компоненты
│   ├── __init__.py
│   ├── config.py           # Конфигурация приложения
│   └── logger.py           # Система логирования
├── docker/
│   ├── docker-compose.yml  # Основной compose файл
│   ├── Dockerfile          # Основной сервис
│   └── requirements.txt    # Зависимости основного сервиса
├── features/
│   ├── __init__.py
│   ├── video_to_audio/
│   │   ├── docker/
│   │   │   ├── Dockerfile  # Конвертер
│   │   │   └── requirements.txt
│   │   ├── converter.py    # Логика конвертации
│   │   └── microservice.py # FastAPI микросервис
│   └── transcription/
│       ├── docker/
│       │   ├── Dockerfile  # Транскрипция
│       │   └── requirements.txt
│       ├── service.py      # Логика транскрипции
│       └── microservice.py # FastAPI микросервис
├── web/
│   └── templates/
│       └── index.html      # Веб-интерфейс
├── __init__.py
└── main.py                 # Основное приложение
```

## 📦 Зависимости по сервисам

### main-app (легкий)
- fastapi, uvicorn, jinja2
- python-multipart, aiofiles
- httpx (для HTTP-клиентов)
- python-json-logger, pydantic

### video-converter (минимальный)
- fastapi, uvicorn
- ffmpeg-python (основная логика)
- python-multipart, aiofiles
- httpx, python-json-logger

### transcription-service (тяжелый)
- fastapi, uvicorn
- whisperx, torch, torchaudio
- librosa, soundfile, ffmpeg-python
- numpy, scipy
- python-multipart, aiofiles, httpx

## 🔄 Жизненный цикл

### Запуск
1. Сборка образов: `docker-compose build`
2. Запуск сервисов: `docker-compose up -d`
3. Проверка health: `docker-compose ps`

### Мониторинг
- Логи: `docker-compose logs -f`
- Статус: `docker-compose ps`
- Health: `curl http://localhost:8000/health`

### Остановка
- Graceful: `docker-compose down`
- Принудительная: `docker-compose down --volumes`

## 🛠️ Устранение неполадок

### Проблемы с зависимостями
```bash
# Пересборка всех образов
docker-compose build --no-cache

# Очистка кэша
docker system prune -a
```

### Проблемы с сетью
```bash
# Проверка сети
docker network ls
docker network inspect media-network

# Пересоздание сети
docker-compose down
docker network prune
docker-compose up -d
```

### Проблемы с volumes
```bash
# Проверка volumes
docker volume ls
docker volume inspect media-processor_whisper-models

# Очистка volumes
docker-compose down --volumes
```

## 📊 Мониторинг и логирование

### Логи
- Централизованное логирование в `/logs/`
- Структурированные JSON логи
- Ротация логов по размеру и времени

### Метрики
- Health endpoints для каждого сервиса
- Статус задач и прогресс
- Использование ресурсов

### Алерты
- Автоматические уведомления при недоступности сервисов
- Мониторинг использования диска
- Отслеживание ошибок

## 🔒 Безопасность

### Изоляция
- Каждый сервис в отдельном контейнере
- Сетевая изоляция через Docker network
- Минимальные привилегии для контейнеров

### Валидация
- Проверка форматов файлов
- Ограничение размера загружаемых файлов
- Санитизация входных данных

### Мониторинг
- Логирование всех операций
- Отслеживание подозрительной активности
- Регулярные обновления образов
