# Скрипт для сборки контейнера транскрипции с GPU поддержкой
Write-Host "🚀 Сборка контейнера транскрипции с GPU поддержкой..." -ForegroundColor Green

# Остановка существующего контейнера если запущен
Write-Host "🛑 Остановка существующего контейнера..." -ForegroundColor Yellow
docker stop transcription-service 2>$null
docker rm transcription-service 2>$null

# Удаление старого образа
Write-Host "🗑️ Удаление старого образа..." -ForegroundColor Yellow
docker rmi transcription-service:latest 2>$null

# Сборка нового образа с GPU поддержкой
Write-Host "🔨 Сборка образа с CUDA поддержкой..." -ForegroundColor Cyan
docker build -f app/features/transcription/docker/Dockerfile -t transcription-service:latest .

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Образ успешно собран!" -ForegroundColor Green
    
    # Проверка доступности GPU
    Write-Host "🔍 Проверка доступности GPU..." -ForegroundColor Cyan
    $gpuCheck = docker run --rm --gpus all nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04 nvidia-smi 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ GPU доступен!" -ForegroundColor Green
        Write-Host $gpuCheck -ForegroundColor Gray
    } else {
        Write-Host "⚠️ GPU недоступен или не настроен" -ForegroundColor Yellow
        Write-Host "💡 Убедитесь что:" -ForegroundColor Cyan
        Write-Host "   - Установлен NVIDIA Container Toolkit" -ForegroundColor Cyan
        Write-Host "   - Docker запущен с поддержкой GPU" -ForegroundColor Cyan
        Write-Host "   - Драйверы NVIDIA установлены" -ForegroundColor Cyan
    }
    
    Write-Host "🎯 Образ готов к запуску с GPU!" -ForegroundColor Green
    Write-Host "💡 Для запуска используйте: .\scripts\docker-run-transcription-gpu.ps1" -ForegroundColor Cyan
    
} else {
    Write-Host "❌ Ошибка сборки образа!" -ForegroundColor Red
    exit 1
}
