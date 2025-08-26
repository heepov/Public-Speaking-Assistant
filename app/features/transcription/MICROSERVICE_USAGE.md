# Transcription Microservice

## Описание
Микросервис для транскрипции аудио файлов с использованием WhisperX и GPU ускорением.

**Порт:** 8002  
**Базовый URL:** http://localhost:8002

## API Endpoints

### Транскрипция аудио файла
```http
POST http://localhost:8002/transcribe
Content-Type: multipart/form-data

Параметры:
- file: аудио файл (MP3, WAV, M4A, FLAC, OGG, AAC)
- task_id: ID задачи (строка)
- model_size: размер модели (tiny/base/small/medium/large-v2/large-v3)
```

**Пример ответа:**
```json
{
  "status": "success",
  "task_id": "test_1234567890",
  "result": {
    "transcription": "Это текст транскрипции на русском языке",
    "detailed_transcription": "Подробная транскрипция с временными метками",
    "saved_files": {
      "txt": "test_1234567890_transcription.txt",
      "json": "test_1234567890_transcription.json"
    }
  },
  "model_used": "base",
  "device_used": "cuda",
  "language": "ru",
  "processing_time": 5.2
}
```

### Пакетная транскрипция
```http
POST http://localhost:8002/transcribe/batch
Content-Type: multipart/form-data

Параметры:
- files: список аудио файлов
- task_id: ID задачи
- model_size: размер модели
```

### Проверка состояния сервиса
```http
GET http://localhost:8002/health
```

**Пример ответа:**
```json
{
  "status": "healthy",
  "service": "transcription",
  "device": "cuda",
  "gpu_status": "available",
  "model_size": "base",
  "language": "ru",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Информация о доступных моделях
```http
GET http://localhost:8002/models
```

**Пример ответа:**
```json
{
  "current_model": "base",
  "current_language": "ru",
  "available_models": ["tiny", "base", "small", "medium", "large-v2", "large-v3"],
  "device": "cuda",
  "gpu_available": true
}
```

### Скачивание результата транскрипции
```http
GET http://localhost:8002/download/{filename}
```

**Параметры:**
- filename: имя файла для скачивания (txt, json, srt)

## Примеры использования

### cURL - Транскрипция аудио
```bash
curl -X POST http://localhost:8002/transcribe \
  -F "file=@audio.wav" \
  -F "task_id=test_123" \
  -F "model_size=base"
```

### cURL - Проверка состояния
```bash
curl http://localhost:8002/health
```

### cURL - Скачивание транскрипции
```bash
# Скачивание TXT файла
curl -O http://localhost:8002/download/test_123_transcription.txt

# Скачивание JSON файла
curl -O http://localhost:8002/download/test_123_transcription.json
```

### Python - Транскрипция аудио
```python
import requests

url = "http://localhost:8002/transcribe"
files = {"file": open("audio.wav", "rb")}
data = {
    "task_id": "test_123",
    "model_size": "base"
}

response = requests.post(url, files=files, data=data)
result = response.json()
print(f"Транскрипция: {result['result']['transcription']}")
```

### Python - Скачивание результатов
```python
import requests

# Скачивание TXT файла
txt_response = requests.get("http://localhost:8002/download/test_123_transcription.txt")
with open("transcription.txt", "wb") as f:
    f.write(txt_response.content)

# Скачивание JSON файла
json_response = requests.get("http://localhost:8002/download/test_123_transcription.json")
with open("transcription.json", "wb") as f:
    f.write(json_response.content)
```

## Размеры моделей

| Модель | Скорость | Точность | Память |
|--------|----------|----------|--------|
| tiny   | Очень быстро | Низкая | ~1GB |
| base   | Быстро | Средняя | ~1GB |
| small  | Средне | Хорошая | ~2GB |
| medium | Медленно | Высокая | ~5GB |
| large-v2 | Очень медленно | Очень высокая | ~10GB |
| large-v3 | Очень медленно | Максимальная | ~10GB |

## Рекомендуемые настройки

### Для быстрой обработки
```json
{
  "model_size": "tiny",
  "language": "ru"
}
```

### Для баланса скорости и точности
```json
{
  "model_size": "base",
  "language": "ru"
}
```

### Для максимальной точности
```json
{
  "model_size": "large-v3",
  "language": "ru"
}
```

## Обработка ошибок

### Ошибка 400 - Неверные параметры
```json
{
  "status": "error",
  "message": "Invalid model size. Supported models: tiny, base, small, medium, large-v2, large-v3"
}
```

### Ошибка 422 - Неподдерживаемый формат
```json
{
  "status": "error",
  "message": "Unsupported audio format. Supported formats: .mp3, .wav, .m4a, .flac, .ogg, .aac"
}
```

### Ошибка 500 - Внутренняя ошибка
```json
{
  "status": "error",
  "message": "Transcription failed: GPU memory error"
}
```

## Интеграция с другими сервисами

### Workflow: Audio → Transcription → Text
1. Получите аудио файл (например, из сервиса конвертации видео)
2. Отправьте аудио на транскрипцию
3. Получите текст и файлы результатов

### Пример полного pipeline
```python
import requests

# 1. Транскрипция аудио
transcription_response = requests.post("http://localhost:8002/transcribe",
    files={"file": open("audio.wav", "rb")},
    data={"task_id": "pipeline_123", "model_size": "base"}
)
result = transcription_response.json()

# 2. Получение результатов
transcription_text = result["result"]["transcription"]
txt_filename = result["result"]["saved_files"]["txt"]
json_filename = result["result"]["saved_files"]["json"]

print(f"Транскрипция: {transcription_text}")

# 3. Скачивание файлов
txt_response = requests.get(f"http://localhost:8002/download/{txt_filename}")
with open(txt_filename, "wb") as f:
    f.write(txt_response.content)

json_response = requests.get(f"http://localhost:8002/download/{json_filename}")
with open(json_filename, "wb") as f:
    f.write(json_response.content)
```

## Форматы выходных файлов

### TXT файл
Простой текст транскрипции без временных меток.

### JSON файл
```json
{
  "task_id": "test_123",
  "filename": "audio.wav",
  "model_used": "base",
  "device_used": "cuda",
  "language": "ru",
  "transcription": "Это текст транскрипции",
  "detailed_transcription": "Подробная транскрипция с метками",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Требования к системе

- **GPU**: NVIDIA GPU с поддержкой CUDA (рекомендуется)
- **Память**: Минимум 4GB RAM, 8GB+ для больших моделей
- **Диск**: Свободное место для кэширования моделей
- **Сеть**: Доступ к интернету для загрузки моделей (только при первом запуске)
