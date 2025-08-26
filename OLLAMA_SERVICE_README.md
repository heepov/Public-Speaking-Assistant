# Ollama Processing Service

Микросервис для обработки текста с помощью Ollama с поддержкой GPU и динамической загрузкой моделей.

## 🚀 Особенности

- ✅ **GPU поддержка** - автоматическое использование NVIDIA GPU
- ✅ **Динамическая загрузка моделей** - модели загружаются автоматически при первом использовании
- ✅ **Сохранение моделей** - модели сохраняются в Docker volume и не удаляются при перезапуске
- ✅ **Быстрая сборка** - оптимизированная сборка контейнера
- ✅ **Множественные модели** - поддержка llama2, llama3 и других моделей
- ✅ **API управление** - REST API для установки/удаления моделей

## 🏗️ Архитектура

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Main App      │    │ Ollama Processing│    │   Ollama        │
│   (FastAPI)     │◄──►│   Microservice   │◄──►│   Server        │
│   Port: 8000    │    │   Port: 8004     │    │   Port: 11434   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                        │
                              │                        │
                              ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   GPU Support   │    │   Models Volume │
                       │   (NVIDIA)      │    │   (Persistent)  │
                       └─────────────────┘    └─────────────────┘
```

## 🛠️ Быстрый старт

### 1. Быстрая сборка и запуск

```powershell
# Запустите скрипт быстрой сборки
.\scripts\docker-build-ollama-fast.ps1
```

Этот скрипт:
- Проверит Docker и NVIDIA Docker
- Соберет образ ollama-processing
- Запустит сервисы ollama и ollama-processing
- Проверит доступность API

### 2. Ручная сборка

```powershell
# Остановить существующие контейнеры
docker-compose -f app/docker/docker-compose.yml stop ollama ollama-processing

# Собрать образ
docker-compose -f app/docker/docker-compose.yml build ollama-processing

# Запустить сервисы
docker-compose -f app/docker/docker-compose.yml up -d ollama ollama-processing
```

## 📡 API Endpoints

### Основные эндпоинты

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| `POST` | `/process` | Обработка текста с автоматической загрузкой модели |
| `GET` | `/models` | Список доступных моделей |
| `POST` | `/models/install` | Установка новой модели |
| `DELETE` | `/models/{model_name}` | Удаление модели |
| `GET` | `/models/info` | Информация о системе и моделях |
| `GET` | `/health` | Проверка здоровья сервиса |

### Примеры использования

#### 1. Обработка текста с автоматической загрузкой модели

```bash
curl -X POST http://localhost:8004/process \
  -F 'prompt=Привет! Расскажи о Python' \
  -F 'task_id=test123' \
  -F 'model_name=llama2'
```

#### 2. Установка модели

```bash
curl -X POST http://localhost:8004/models/install \
  -F 'model_name=llama3:8b'
```

#### 3. Список доступных моделей

```bash
curl http://localhost:8004/models
```

#### 4. Информация о системе

```bash
curl http://localhost:8004/models/info
```

## 🤖 Поддерживаемые модели

### Llama 2
- `llama2` - базовая модель (7B)
- `llama2:7b` - 7B параметров
- `llama2:13b` - 13B параметров  
- `llama2:70b` - 70B параметров

### Llama 3
- `llama3` - базовая модель (8B)
- `llama3:8b` - 8B параметров
- `llama3:70b` - 70B параметров

### Другие модели
- `mistral` - Mistral 7B
- `codellama` - Code Llama
- `neural-chat` - Intel Neural Chat
- `vicuna` - Vicuna

## 🧪 Тестирование

### Автоматическое тестирование

```powershell
# Запустите скрипт тестирования
.\scripts\test-ollama-api.ps1
```

Этот скрипт:
- Проверит доступность API
- Протестирует установку различных моделей
- Выполнит обработку текста с каждой моделью
- Покажет результаты тестирования

### Ручное тестирование

```powershell
# Проверка здоровья API
Invoke-RestMethod -Uri "http://localhost:8004/health"

# Список моделей
Invoke-RestMethod -Uri "http://localhost:8004/models"

# Установка модели
$body = @{ model_name = "llama2" }
Invoke-RestMethod -Uri "http://localhost:8004/models/install" -Method POST -Form $body

# Обработка текста
$body = @{
    prompt = "Привет! Как дела?"
    task_id = "test123"
    model_name = "llama2"
}
Invoke-RestMethod -Uri "http://localhost:8004/process" -Method POST -Form $body
```

## 🔧 Конфигурация

### Переменные окружения

| Переменная | Значение по умолчанию | Описание |
|------------|----------------------|----------|
| `OLLAMA_HOST` | `ollama:11434` | Адрес Ollama сервера |
| `PORT` | `8004` | Порт микросервиса |
| `CUDA_VISIBLE_DEVICES` | `0` | GPU устройства |
| `LOG_LEVEL` | `INFO` | Уровень логирования |

### Docker Volumes

- `ollama-models` - постоянное хранение моделей
- `uploads` - входные файлы
- `outputs` - результаты обработки
- `logs` - логи приложения

## 🐛 Устранение неполадок

### Проблемы с GPU

```powershell
# Проверка NVIDIA Docker
docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi

# Проверка GPU в контейнере
docker exec -it ollama-processing nvidia-smi
```

### Проблемы с моделями

```powershell
# Проверка доступных моделей
curl http://localhost:11434/api/tags

# Проверка статуса Ollama
docker logs ollama

# Перезапуск Ollama
docker-compose -f app/docker/docker-compose.yml restart ollama
```

### Проблемы с API

```powershell
# Проверка логов микросервиса
docker logs ollama-processing

# Проверка доступности API
curl http://localhost:8004/health

# Перезапуск микросервиса
docker-compose -f app/docker/docker-compose.yml restart ollama-processing
```

## 📊 Мониторинг

### Логи

```powershell
# Логи Ollama сервера
docker logs -f ollama

# Логи микросервиса
docker logs -f ollama-processing

# Все логи
docker-compose -f app/docker/docker-compose.yml logs -f
```

### Статус сервисов

```powershell
# Статус контейнеров
docker-compose -f app/docker/docker-compose.yml ps

# Использование ресурсов
docker stats ollama ollama-processing
```

## 🔄 Обновление

### Обновление кода

```powershell
# Остановить сервисы
docker-compose -f app/docker/docker-compose.yml stop ollama-processing

# Пересобрать образ
docker-compose -f app/docker/docker-compose.yml build ollama-processing

# Запустить сервисы
docker-compose -f app/docker/docker-compose.yml up -d ollama-processing
```

### Обновление моделей

```powershell
# Обновить конкретную модель
curl -X POST http://localhost:8004/models/install -F 'model_name=llama2'

# Удалить старую модель
curl -X DELETE http://localhost:8004/models/llama2:old
```

## 📝 Примеры использования

### Python клиент

```python
import requests

# Обработка текста
response = requests.post('http://localhost:8004/process', data={
    'prompt': 'Объясни квантовую физику простыми словами',
    'task_id': 'quantum_physics',
    'model_name': 'llama3:8b'
})

print(response.json()['result'])

# Установка модели
requests.post('http://localhost:8004/models/install', data={
    'model_name': 'llama3:70b'
})
```

### JavaScript клиент

```javascript
// Обработка текста
const response = await fetch('http://localhost:8004/process', {
    method: 'POST',
    body: new FormData({
        prompt: 'Напиши стихотворение о программировании',
        task_id: 'poem',
        model_name: 'llama2'
    })
});

const result = await response.json();
console.log(result.result);
```

## 🎯 Преимущества

1. **Быстрая разработка** - не нужно ждать 15 минут на пересборку
2. **Экономия места** - модели загружаются только при необходимости
3. **Гибкость** - легко переключаться между моделями
4. **Надежность** - модели сохраняются между перезапусками
5. **Производительность** - полная поддержка GPU
6. **Масштабируемость** - можно легко добавлять новые модели

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `docker logs ollama-processing`
2. Убедитесь, что GPU доступен: `nvidia-smi`
3. Проверьте доступность API: `curl http://localhost:8004/health`
4. Перезапустите сервисы при необходимости
