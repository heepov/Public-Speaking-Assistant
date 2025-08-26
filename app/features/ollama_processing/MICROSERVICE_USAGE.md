# Ollama Processing Microservice

## Описание
Микросервис для обработки текста с использованием Ollama и GPU ускорением.

**Порт:** 8004  
**Базовый URL:** http://localhost:8004

## API Endpoints

### Обработка текста с помощью LLM
```http
POST http://localhost:8004/process
Content-Type: application/json

{
  "text": "Текст для обработки",
  "model": "llama2",
  "task_id": "test_1234567890",
  "parameters": {
    "temperature": 0.7,
    "max_tokens": 1000,
    "top_p": 0.9
  }
}
```

**Пример ответа:**
```json
{
  "status": "success",
  "task_id": "test_1234567890",
  "result": {
    "processed_text": "Обработанный текст с помощью LLM",
    "model_response": "Полный ответ модели",
    "saved_files": {
      "txt": "test_1234567890_processed.txt",
      "json": "test_1234567890_processed.json"
    }
  },
  "model_used": "llama2",
  "device_used": "cuda",
  "processing_time": 2.5
}
```

### Пакетная обработка текста
```http
POST http://localhost:8004/process/batch
Content-Type: application/json

{
  "texts": ["Текст 1", "Текст 2", "Текст 3"],
  "model": "llama2",
  "task_id": "batch_test_1234567890",
  "parameters": {
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

### Проверка состояния сервиса
```http
GET http://localhost:8004/health
```

**Пример ответа:**
```json
{
  "status": "healthy",
  "service": "ollama_processing",
  "device": "cuda",
  "gpu_status": "available",
  "ollama_host": "localhost:11434",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Информация о доступных моделях
```http
GET http://localhost:8004/models
```

**Пример ответа:**
```json
{
  "available_models": [
    {
      "name": "llama2",
      "size": "3.8GB",
      "modified_at": "2024-01-15T10:00:00Z"
    },
    {
      "name": "mistral",
      "size": "4.1GB",
      "modified_at": "2024-01-15T09:00:00Z"
    }
  ],
  "device": "cuda",
  "gpu_available": true
}
```

### Загрузка новой модели
```http
POST http://localhost:8004/models/pull
Content-Type: application/json

{
  "model_name": "llama2:13b"
}
```

### Скачивание результата обработки
```http
GET http://localhost:8004/download/{filename}
```

**Параметры:**
- filename: имя файла для скачивания (txt, json)

## Примеры использования

### cURL - Обработка текста
```bash
curl -X POST http://localhost:8004/process \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Привет, как дела?",
    "model": "llama2",
    "task_id": "test_123",
    "parameters": {
      "temperature": 0.7,
      "max_tokens": 100
    }
  }'
```

### cURL - Пакетная обработка
```bash
curl -X POST http://localhost:8004/process/batch \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Текст 1", "Текст 2"],
    "model": "llama2",
    "task_id": "batch_test",
    "parameters": {
      "temperature": 0.7
    }
  }'
```

### cURL - Проверка здоровья
```bash
curl -X GET http://localhost:8004/health
```

### cURL - Список моделей
```bash
curl -X GET http://localhost:8004/models
```

### cURL - Загрузка модели
```bash
curl -X POST http://localhost:8004/models/pull \
  -H "Content-Type: application/json" \
  -d '{"model_name": "llama2:13b"}'
```

## Python примеры

### Обработка текста
```python
import requests
import json

url = "http://localhost:8004/process"
data = {
    "text": "Привет, как дела?",
    "model": "llama2",
    "task_id": "test_123",
    "parameters": {
        "temperature": 0.7,
        "max_tokens": 100
    }
}

response = requests.post(url, json=data)
result = response.json()
print(result)
```

### Пакетная обработка
```python
import requests
import json

url = "http://localhost:8004/process/batch"
data = {
    "texts": ["Текст 1", "Текст 2", "Текст 3"],
    "model": "llama2",
    "task_id": "batch_test",
    "parameters": {
        "temperature": 0.7,
        "max_tokens": 100
    }
}

response = requests.post(url, json=data)
result = response.json()
print(result)
```

## Поддерживаемые модели

- **llama2** - Llama 2 (7B параметров)
- **llama2:13b** - Llama 2 (13B параметров)
- **mistral** - Mistral (7B параметров)
- **codellama** - Code Llama
- **neural-chat** - Intel Neural Chat
- И любые другие модели из Ollama Hub

## Параметры модели

- **temperature** (0.0-1.0): Контролирует случайность ответов
- **max_tokens** (1-4096): Максимальное количество токенов в ответе
- **top_p** (0.0-1.0): Nucleus sampling
- **top_k** (1-100): Top-k sampling
- **repeat_penalty** (0.0-2.0): Штраф за повторения

## Обработка ошибок

### Ошибка модели не найдена
```json
{
  "status": "error",
  "error": "Model 'unknown_model' not found",
  "available_models": ["llama2", "mistral"]
}
```

### Ошибка Ollama сервера
```json
{
  "status": "error",
  "error": "Ollama server is not available",
  "ollama_host": "localhost:11434"
}
```

### Ошибка GPU
```json
{
  "status": "error",
  "error": "GPU not available, falling back to CPU",
  "device_used": "cpu"
}
```

## Мониторинг и логи

- Все запросы логируются с временными метками
- Информация о GPU/CPU использовании
- Статистика обработки запросов
- Ошибки и предупреждения

## Web-интерфейс

Сервис предоставляет веб-интерфейс для тестирования:
- **URL:** http://localhost:8004
- **Swagger UI:** http://localhost:8004/docs
- **ReDoc:** http://localhost:8004/redoc
