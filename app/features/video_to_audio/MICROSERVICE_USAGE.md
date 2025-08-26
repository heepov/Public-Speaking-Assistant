# Video to Audio Converter Microservice

## Описание
Микросервис для конвертации видео файлов в аудио с использованием FFmpeg.

**Порт:** 8003  
**Базовый URL:** http://localhost:8003

## API Endpoints

### Конвертация видео в аудио
```http
POST http://localhost:8003/convert
Content-Type: multipart/form-data

Параметры:
- file: видео файл (MP4, AVI, MOV, MKV, WMV, FLV, WebM)
- task_id: ID задачи (строка)
- audio_format: формат аудио (wav/mp3/m4a/flac/ogg)
- sample_rate: частота дискретизации (8000/16000/22050/44100/48000)
- channels: количество каналов (1/2)
- bitrate: битрейт в kbps (32-320)
```

**Пример ответа:**
```json
{
  "status": "success",
  "task_id": "test_1234567890",
  "original_filename": "video.mp4",
  "output_filename": "test_1234567890_audio.wav",
  "output_file": "test_1234567890_audio.wav",
  "processing_time": 2.5,
  "audio_settings": {
    "format": "wav",
    "sample_rate": 16000,
    "channels": 1,
    "bitrate": 128
  }
}
```

### Пакетная конвертация
```http
POST http://localhost:8003/convert/batch
Content-Type: multipart/form-data

Параметры:
- files: список видео файлов
- task_id: ID задачи
- audio_format: формат аудио
- sample_rate: частота дискретизации
- channels: количество каналов
- bitrate: битрейт
```

### Проверка состояния сервиса
```http
GET http://localhost:8003/health
```

**Пример ответа:**
```json
{
  "status": "healthy",
  "service": "video_converter",
  "ffmpeg_status": "available",
  "ffmpeg_path": "/usr/bin/ffmpeg",
  "supported_video_formats": [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"],
  "optimal_audio_settings": {
    "format": "wav",
    "sample_rate": 16000,
    "channels": 1,
    "bitrate": 128
  }
}
```

### Информация о поддерживаемых форматах
```http
GET http://localhost:8003/formats
```

**Пример ответа:**
```json
{
  "video_formats": [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"],
  "audio_formats": [".wav", ".mp3", ".m4a", ".flac", ".ogg"],
  "optimal_settings": {
    "format": "wav",
    "sample_rate": 16000,
    "channels": 1,
    "bitrate": 128
  }
}
```

### Скачивание результата
```http
GET http://localhost:8003/download/{filename}
```

**Параметры:**
- filename: имя файла для скачивания

## Примеры использования

### cURL - Конвертация видео
```bash
curl -X POST http://localhost:8003/convert \
  -F "file=@video.mp4" \
  -F "task_id=test_123" \
  -F "audio_format=wav" \
  -F "sample_rate=16000" \
  -F "channels=1" \
  -F "bitrate=128"
```

### cURL - Проверка состояния
```bash
curl http://localhost:8003/health
```

### cURL - Скачивание файла
```bash
curl -O http://localhost:8003/download/test_123_audio.wav
```

### Python - Конвертация видео
```python
import requests

url = "http://localhost:8003/convert"
files = {"file": open("video.mp4", "rb")}
data = {
    "task_id": "test_123",
    "audio_format": "wav",
    "sample_rate": "16000",
    "channels": "1",
    "bitrate": "128"
}

response = requests.post(url, files=files, data=data)
result = response.json()
print(f"Файл сохранен: {result['output_filename']}")
```

### Python - Скачивание результата
```python
import requests

filename = "test_123_audio.wav"
url = f"http://localhost:8003/download/{filename}"

response = requests.get(url)
with open(filename, "wb") as f:
    f.write(response.content)
```

## Рекомендуемые настройки для транскрипции

Для оптимальной работы с сервисом транскрипции используйте:

```json
{
  "audio_format": "wav",
  "sample_rate": 16000,
  "channels": 1,
  "bitrate": 128
}
```

## Обработка ошибок

### Ошибка 400 - Неверные параметры
```json
{
  "status": "error",
  "message": "Invalid audio format. Supported formats: wav, mp3, m4a, flac, ogg"
}
```

### Ошибка 422 - Неподдерживаемый формат
```json
{
  "status": "error",
  "message": "Unsupported video format. Supported formats: .mp4, .avi, .mov, .mkv, .wmv, .flv, .webm"
}
```

### Ошибка 500 - Внутренняя ошибка
```json
{
  "status": "error",
  "message": "Conversion failed: FFmpeg error"
}
```

## Интеграция с другими сервисами

### Workflow: Video → Audio → Transcription
1. Конвертируйте видео в аудио через этот сервис
2. Используйте полученное аудио в сервисе транскрипции
3. Получите текст транскрипции

### Пример полного pipeline
```python
import requests

# 1. Конвертация видео в аудио
video_response = requests.post("http://localhost:8003/convert", 
    files={"file": open("video.mp4", "rb")},
    data={"task_id": "pipeline_123", "audio_format": "wav", "sample_rate": "16000", "channels": "1"}
)
audio_result = video_response.json()
audio_filename = audio_result["output_filename"]

# 2. Транскрипция аудио
transcription_response = requests.post("http://localhost:8002/transcribe",
    files={"file": open(audio_filename, "rb")},
    data={"task_id": "pipeline_123", "model_size": "base"}
)
transcription_result = transcription_response.json()
print(f"Транскрипция: {transcription_result['transcription']}")
```
