# Скрипт для проверки доступности GPU
Write-Host "🔍 Проверка доступности GPU..." -ForegroundColor Green

# Проверка NVIDIA драйверов в системе
Write-Host "📊 Проверка NVIDIA драйверов в системе:" -ForegroundColor Cyan
try {
    $nvidiaSmi = nvidia-smi 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ NVIDIA драйверы установлены:" -ForegroundColor Green
        Write-Host $nvidiaSmi -ForegroundColor Gray
    } else {
        Write-Host "❌ NVIDIA драйверы не найдены" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Команда nvidia-smi недоступна" -ForegroundColor Red
}

# Проверка Docker с GPU поддержкой
Write-Host "`n🐳 Проверка Docker с GPU поддержкой:" -ForegroundColor Cyan
try {
    $dockerGpu = docker run --rm --gpus all nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04 nvidia-smi 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker поддерживает GPU:" -ForegroundColor Green
        Write-Host $dockerGpu -ForegroundColor Gray
    } else {
        Write-Host "❌ Docker не поддерживает GPU" -ForegroundColor Red
        Write-Host "💡 Установите NVIDIA Container Toolkit:" -ForegroundColor Yellow
        Write-Host "   https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Ошибка проверки Docker GPU" -ForegroundColor Red
}

# Проверка PyTorch с CUDA
Write-Host "`n🔥 Проверка PyTorch с CUDA:" -ForegroundColor Cyan
try {
    $pytorchCheck = docker run --rm --gpus all transcription-service:latest python3 -c "
import torch
print(f'PyTorch версия: {torch.__version__}')
print(f'CUDA доступна: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU устройство: {torch.cuda.get_device_name(0)}')
    print(f'GPU память: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} ГБ')
else:
    print('CUDA недоступна')
" 2>$null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ PyTorch с CUDA работает:" -ForegroundColor Green
        Write-Host $pytorchCheck -ForegroundColor Gray
    } else {
        Write-Host "❌ Ошибка проверки PyTorch" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Образ transcription-service:latest не найден" -ForegroundColor Red
    Write-Host "💡 Сначала соберите образ: .\scripts\docker-build-transcription-gpu.ps1" -ForegroundColor Yellow
}

Write-Host "`n🎯 Проверка завершена!" -ForegroundColor Green
