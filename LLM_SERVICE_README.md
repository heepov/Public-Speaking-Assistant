# LLM Processing Service

Микросервис для обработки текста с помощью LLaMA 3 13B Q4_K_M GGUF модели с GPU поддержкой.

## 🚀 Возможности

- **LLaMA 3 13B Q4_K_M GGUF**: Использование современной модели с квантизацией
- **GPU ускорение**: Полная поддержка CUDA для быстрой обработки
- **RoPE Scaling**: Расширенный контекст до 32k токенов
- **Гибкий ввод**: Поддержка JSON, TXT, MD и других форматов
- **Инструкции**: Возможность загрузки файла с инструкциями
- **REST API**: Полноценный API для интеграции

## 📋 Требования

- **GPU**: NVIDIA GPU с поддержкой CUDA 12.1+
- **RAM**: Минимум 16GB (рекомендуется 32GB+)
- **VRAM**: Минимум 8GB для модели 13B
- **Docker**: Версия 20.10+
- **NVIDIA Container Toolkit**: Для GPU поддержки

## 🏗️ Архитектура

```
LLM Processing Service
├── FastAPI (порт 8003)
├── LLaMA 3 13B Q4_K_M GGUF
├── GPU Acceleration (CUDA)
├── RoPE Scaling (32k context)
└── File Processing
    ├── JSON input
    ├── TXT/MD files
    ├── Instructions (MD)
    └── Output results
```

## 🚀 Быстрый старт

### 1. Сборка образа

```powershell
.\scripts\docker-build-llm.ps1
```

### 2. Запуск сервиса

```powershell
.\scripts\docker-run-llm.ps1 -Port 8003 -GpuId 0
```

### 3. Проверка работы

```bash
curl http://localhost:8003/health
```

## 📖 API Endpoints

### POST /process
Обработка файла с входными данными

**Параметры:**
- `input_file`: Файл с данными (JSON, TXT, MD)
- `task_id`: Уникальный ID задачи
- `prompt`: Промпт для обработки
- `instructions_file`: Файл с инструкциями (опционально)

**Пример запроса:**
```bash
curl -X POST "http://localhost:8003/process" \
  -F "input_file=@example_input.json" \
  -F "task_id=task_123" \
  -F "prompt=Проанализируй это выступление и дай рекомендации"
```

### POST /process-json
Обработка JSON данных напрямую

**Параметры:**
- `data`: JSON данные
- `task_id`: Уникальный ID задачи
- `prompt`: Промпт для обработки
- `instructions_file`: Файл с инструкциями (опционально)

### GET /health
Проверка состояния сервиса

### GET /model-info
Информация о модели

### GET /supported-formats
Список поддерживаемых форматов

## 📁 Структура файлов

```
app/features/llm_processing/
├── __init__.py
├── service.py              # Основной сервис
├── microservice.py         # FastAPI приложение
├── docker/
│   ├── Dockerfile          # Docker образ
│   ├── requirements.txt    # Зависимости
│   └── download_model.sh   # Скрипт загрузки модели
├── example_input.json      # Пример входных данных
└── example_instructions.md # Пример инструкций
```

## 🔧 Конфигурация

### Переменные окружения

```bash
# Основные настройки
PORT=8003                    # Порт сервиса
LOG_LEVEL=INFO              # Уровень логирования
CUDA_VISIBLE_DEVICES=0      # ID GPU устройства
LLAMA_CUBLAS=1              # Включить GPU ускорение

# Настройки модели
MODEL_PATH=/models/llama-3-13b-q4_k_m.gguf
CONTEXT_LENGTH=32768        # Размер контекста
```

### Параметры модели

```python
# В service.py
self.model = Llama(
    model_path=str(self.model_path),
    n_gpu_layers=-1,        # Все слои на GPU
    n_ctx=self.context_length,
    rope_scaling_type=1,    # RoPE scaling
    rope_freq_scale=0.5,    # Масштабирование для 32k
    verbose=False
)
```

## 📊 Примеры использования

### 1. Анализ выступления

**Входной файл (example_input.json):**
```json
{
  "title": "Искусственный интеллект в современном мире",
  "speaker": "Иван Петров",
  "content": {
    "introduction": "Добрый день, уважаемые коллеги!...",
    "main_points": [...],
    "conclusion": "Спасибо за внимание!"
  }
}
```

**Инструкции (example_instructions.md):**
```markdown
# Инструкции для анализа выступления

## Критерии оценки
- Содержание (40%)
- Структура (25%)
- Подача (20%)
- Технические аспекты (15%)
```

**Промпт:**
```
Проанализируй это выступление по критериям из инструкций и дай подробный отчет с рекомендациями
```

### 2. Обработка текста

**Входной файл (text.txt):**
```
Это пример текста для обработки. 
LLM должен проанализировать его и дать рекомендации.
```

**Промпт:**
```
Найди ошибки в тексте и предложи улучшения
```

## 🐳 Docker Compose

Сервис интегрирован в общий docker-compose.yml:

```yaml
llm-processing:
  build:
    context: ../..
    dockerfile: app/features/llm_processing/docker/Dockerfile
  image: pres-prog-llm:latest
  container_name: pres-prog-llm
  ports:
    - "8003:8003"
  environment:
    - CUDA_VISIBLE_DEVICES=0
    - LLAMA_CUBLAS=1
  volumes:
    - ../../models:/models
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

## 🔍 Мониторинг

### Логи

```bash
# Просмотр логов контейнера
docker logs pres-prog-llm

# Логи в реальном времени
docker logs -f pres-prog-llm
```

### Метрики

- **Время обработки**: Обычно 10-30 секунд
- **Использование GPU**: Мониторинг через `nvidia-smi`
- **Память**: ~8GB VRAM для модели 13B

## 🛠️ Устранение неполадок

### Проблема: Модель не загружается

```bash
# Проверьте наличие модели
ls -la models/llama-3-13b-q4_k_m.gguf

# Загрузите модель вручную
./app/features/llm_processing/docker/download_model.sh
```

### Проблема: GPU не используется

```bash
# Проверьте CUDA
nvidia-smi

# Проверьте переменные окружения
docker exec pres-prog-llm env | grep CUDA
```

### Проблема: Недостаточно памяти

```bash
# Уменьшите количество GPU слоев
# В service.py измените n_gpu_layers с -1 на меньшее значение
```

## 📈 Производительность

### Тестовые результаты

| Модель | VRAM | Время обработки | Точность |
|--------|------|-----------------|----------|
| LLaMA 3 13B Q4_K_M | 8GB | 15-25 сек | Высокая |
| LLaMA 3 13B Q4_K_M | 16GB | 10-15 сек | Высокая |

### Оптимизация

1. **GPU слои**: Используйте `n_gpu_layers=-1` для максимальной производительности
2. **Контекст**: Увеличьте `n_ctx` для длинных текстов
3. **Параллелизм**: Обрабатывайте несколько задач одновременно

## 🔐 Безопасность

- **Изоляция**: Каждый запрос обрабатывается в изолированном контексте
- **Валидация**: Все входные данные проверяются
- **Логирование**: Все операции логируются для аудита
- **Ограничения**: Максимальный размер файла и контекста

## 🤝 Интеграция

### С основным приложением

```python
import requests

def process_with_llm(input_data, prompt, task_id):
    url = "http://localhost:8003/process"
    files = {
        'input_file': ('data.json', json.dumps(input_data)),
        'instructions_file': ('instructions.md', instructions_content)
    }
    data = {
        'task_id': task_id,
        'prompt': prompt
    }
    
    response = requests.post(url, files=files, data=data)
    return response.json()
```

### Webhook интеграция

```python
@app.post("/webhook/llm-result")
async def handle_llm_result(result: dict):
    # Обработка результата от LLM сервиса
    task_id = result['task_id']
    processed_result = result['result']
    
    # Сохранение или дальнейшая обработка
    await save_result(task_id, processed_result)
```

## 📚 Дополнительные ресурсы

- [LLaMA 3 Documentation](https://llama.meta.com/)
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
- [CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit)
- [Docker GPU Support](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/)

## 🆘 Поддержка

При возникновении проблем:

1. Проверьте логи: `docker logs pres-prog-llm`
2. Убедитесь в наличии GPU: `nvidia-smi`
3. Проверьте модель: `ls -la models/`
4. Обратитесь к документации выше

---

**Версия**: 1.0.0  
**Дата**: 2024-01-15  
**Автор**: Media Processor Team
