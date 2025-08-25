# Скрипт для запуска контейнера транскрипции с GPU поддержкой
Write-Host "🚀 Запуск контейнера транскрипции с GPU поддержкой..." -ForegroundColor Green

# Проверка существования образа
$imageExists = docker images transcription-service:latest --format "table {{.Repository}}:{{.Tag}}" | Select-String "transcription-service:latest"

if (-not $imageExists) {
    Write-Host "❌ Образ transcription-service:latest не найден!" -ForegroundColor Red
    Write-Host "💡 Сначала соберите образ: .\scripts\docker-build-transcription-gpu.ps1" -ForegroundColor Cyan
    exit 1
}

# Остановка существующего контейнера если запущен
Write-Host "🛑 Остановка существующего контейнера..." -ForegroundColor Yellow
docker stop transcription-service 2>$null
docker rm transcription-service 2>$null

# Создание необходимых директорий
Write-Host "📁 Создание директорий..." -ForegroundColor Cyan
if (-not (Test-Path "uploads")) { New-Item -ItemType Directory -Path "uploads" }
if (-not (Test-Path "outputs")) { New-Item -ItemType Directory -Path "outputs" }
if (-not (Test-Path "logs")) { New-Item -ItemType Directory -Path "logs" }

# Запуск контейнера с GPU поддержкой
Write-Host "🎯 Запуск контейнера с GPU..." -ForegroundColor Cyan
docker run -d `
    --name transcription-service `
    --gpus all `
    -p 8001:8001 `
    -v "${PWD}/uploads:/app/uploads" `
    -v "${PWD}/outputs:/app/outputs" `
    -v "${PWD}/logs:/app/logs" `
    -e CUDA_VISIBLE_DEVICES=0 `
    transcription-service:latest

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Контейнер успешно запущен!" -ForegroundColor Green
    
    # Проверка статуса
    Start-Sleep -Seconds 3
    $status = docker ps --filter "name=transcription-service" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    Write-Host "📊 Статус контейнера:" -ForegroundColor Cyan
    Write-Host $status -ForegroundColor Gray
    
    # Проверка логов
    Write-Host "📋 Логи запуска:" -ForegroundColor Cyan
    docker logs transcription-service --tail 10
    
    Write-Host "🎯 Сервис транскрипции доступен на http://localhost:8001" -ForegroundColor Green
    Write-Host "📖 Документация API: http://localhost:8001/docs" -ForegroundColor Cyan
    
} else {
    Write-Host "❌ Ошибка запуска контейнера!" -ForegroundColor Red
    
    # Показываем логи ошибки
    Write-Host "📋 Логи ошибки:" -ForegroundColor Red
    docker logs transcription-service --tail 20 2>$null
    
    exit 1
}
