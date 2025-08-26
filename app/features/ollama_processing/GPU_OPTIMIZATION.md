# 🚀 Оптимизация GPU для Ollama

## 📋 Что добавлено

В код добавлена автоматическая оптимизация параметров GPU для увеличения загрузки GPU и снижения нагрузки на CPU.

### 🔧 Основные параметры

- **`num_gpu_layers`** - количество слоев модели на GPU (основной параметр для загрузки GPU)
- **`num_ctx`** - размер контекста (влияет на память)
- **`num_thread`** - количество CPU потоков

## 🎯 Рекомендации для RTX 2080 Ti (11 GB)

### ✅ Оптимальные настройки

```json
{
  "num_gpu_layers": 32,
  "num_ctx": 4096,
  "num_thread": 8,
  "temperature": 0.95,
  "top_p": 0.9,
  "num_predict": 800
}
```

### 🔍 Как проверить загрузку GPU

1. **Windows (PowerShell):**
```powershell
nvidia-smi -l 1
```

2. **Проверить в коде:**
```python
import torch
print(f"GPU память: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
print(f"GPU память (всего): {torch.cuda.memory_reserved() / 1024**3:.2f} GB")
```

## 🧪 Тестирование

Запустите тестовый скрипт:

```bash
cd app/features/ollama_processing
python test_gpu_optimization.py
```

## 📊 Автоматическая оптимизация

Код автоматически определяет вашу GPU и устанавливает оптимальные параметры:

| GPU Память | num_gpu_layers | num_ctx | num_thread |
|------------|----------------|---------|------------|
| ≥24 GB     | 40            | 8192    | 12         |
| ≥16 GB     | 35            | 6144    | 10         |
| ≥12 GB     | 32            | 4096    | 8          |
| ≥8 GB      | 28            | 3072    | 6          |
| <8 GB      | 20            | 2048    | 4          |

## ⚠️ Важные моменты

1. **Для gpt-oss:20b** - модель большая, поэтому используйте `num_gpu_layers: 32` максимум
2. **Если вылетает по памяти** - уменьшите `num_gpu_layers` на 4-8
3. **Для стабильности** - начните с `num_gpu_layers: 28`

## 🔧 Ручная настройка

Создайте файл с параметрами:

```json
{
  "num_gpu_layers": 32,
  "num_ctx": 4096,
  "num_thread": 8,
  "temperature": 0.95,
  "top_p": 0.9,
  "num_predict": 800
}
```

И передайте его в `model_params` при вызове `process_text()`.

## 🚨 Устранение проблем

### Проблема: "CUDA out of memory"
**Решение:** Уменьшите `num_gpu_layers` на 4-8

### Проблема: Низкая загрузка GPU
**Решение:** Увеличьте `num_gpu_layers` (но не больше 40)

### Проблема: Медленная работа
**Решение:** Увеличьте `num_thread` и `num_ctx`

## 📈 Мониторинг производительности

Добавьте в код для мониторинга:

```python
import torch
import psutil

# GPU мониторинг
gpu_memory = torch.cuda.memory_allocated() / 1024**3
print(f"GPU память: {gpu_memory:.2f} GB")

# CPU мониторинг
cpu_percent = psutil.cpu_percent()
print(f"CPU загрузка: {cpu_percent}%")
```
