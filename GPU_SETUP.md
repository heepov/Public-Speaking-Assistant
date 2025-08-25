# 🚀 Настройка GPU для сервиса транскрипции

## 📋 Требования

### Системные требования
- NVIDIA GPU с поддержкой CUDA
- NVIDIA драйверы версии 450+ 
- Docker Desktop с поддержкой GPU
- NVIDIA Container Toolkit

### Рекомендуемые GPU
- **Минимум**: GTX 1060 6GB / RTX 2060 6GB
- **Рекомендуется**: RTX 3070 8GB / RTX 3080 10GB / RTX 4080 16GB
- **Оптимально**: RTX 4090 24GB / A100 40GB

## 🔧 Установка NVIDIA Container Toolkit

### Windows
1. Установите [NVIDIA драйверы](https://www.nvidia.com/Download/index.aspx)
2. Установите [Docker Desktop](https://www.docker.com/products/docker-desktop/)
3. Установите [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html#docker)

### Linux
```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

## 🧪 Проверка установки

### 1. Проверка драйверов
```bash
nvidia-smi
```

### 2. Проверка Docker GPU
```bash
docker run --rm --gpus all nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04 nvidia-smi
```

### 3. Автоматическая проверка
```powershell
.\scripts\check-gpu.ps1
```

## 🚀 Запуск с GPU

### 1. Сборка образа с GPU поддержкой
```powershell
.\scripts\docker-build-transcription-gpu.ps1
```

### 2. Запуск контейнера с GPU
```powershell
.\scripts\docker-run-transcription-gpu.ps1
```

### 3. Проверка работы GPU
```powershell
# Проверка логов контейнера
docker logs transcription-service

# Проверка использования GPU
docker exec transcription-service nvidia-smi
```

## 📊 Производительность

### Сравнение CPU vs GPU

| Модель | CPU (Intel i7) | GPU (RTX 3080) | Ускорение |
|--------|----------------|----------------|-----------|
| tiny   | ~30 сек        | ~5 сек         | 6x        |
| base   | ~60 сек        | ~10 сек        | 6x        |
| small  | ~120 сек       | ~20 сек        | 6x        |
| medium | ~300 сек       | ~50 сек        | 6x        |
| large  | ~600 сек       | ~100 сек       | 6x        |

*Время указано для аудио файла длиной 1 минута*

## 🔧 Настройки

### Размер модели
В файле `app/features/transcription/service.py`:
```python
self.model_size = "base"  # tiny, base, small, medium, large-v2, large-v3
```

### Тип вычислений
- **GPU**: `float16` (автоматически)
- **CPU**: `int8` (автоматически)

### Batch size
- **GPU**: 16 (автоматически)
- **CPU**: 4 (автоматически)

## 🐛 Устранение проблем

### Ошибка: "CUDA out of memory"
```bash
# Уменьшите batch size в коде
batch_size=8 if self.device == "cuda" else 4

# Или используйте меньшую модель
self.model_size = "small"
```

### Ошибка: "NVIDIA Container Toolkit not found"
```bash
# Переустановите NVIDIA Container Toolkit
# Перезапустите Docker Desktop
```

### Ошибка: "No CUDA devices available"
```bash
# Проверьте драйверы NVIDIA
nvidia-smi

# Проверьте Docker GPU поддержку
docker run --rm --gpus all nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04 nvidia-smi
```

## 📈 Мониторинг

### Использование GPU
```bash
# В реальном времени
watch -n 1 nvidia-smi

# В контейнере
docker exec transcription-service nvidia-smi
```

### Логи транскрипции
```bash
docker logs -f transcription-service
```

## 🎯 Оптимизация

### Для максимальной производительности:
1. Используйте GPU с 8GB+ памяти
2. Выберите модель `medium` или `large`
3. Убедитесь что GPU не используется другими процессами
4. Используйте SSD для хранения файлов

### Для экономии ресурсов:
1. Используйте модель `tiny` или `base`
2. Ограничьте batch size
3. Используйте CPU для небольших файлов

## 📚 Дополнительные ресурсы

- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/)
- [WhisperX Documentation](https://github.com/m-bain/whisperX)
- [PyTorch CUDA](https://pytorch.org/docs/stable/cuda.html)

