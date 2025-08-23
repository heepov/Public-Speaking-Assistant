# Скрипт для запуска транскрипции
Write-Host "🚀 Запуск транскрипции..." -ForegroundColor Green

# Проверяем наличие образа
$imageExists = docker images --format "table {{.Repository}}:{{.Tag}}" | Select-String "media-processor-transcription:latest"
if (-not $imageExists) {
    Write-Host "❌ Образ media-processor-transcription:latest не найден!" -ForegroundColor Red
    Write-Host "🔨 Сначала соберите образ: ./scripts/docker-build-transcription.ps1" -ForegroundColor Yellow
    exit 1
}

# Останавливаем существующий контейнер
Write-Host "🛑 Останавливаем существующий контейнер..." -ForegroundColor Yellow
docker stop media-processor-transcription 2>$null
docker rm media-processor-transcription 2>$null

# Запускаем транскрипцию
Write-Host "🚀 Запускаем транскрипцию..." -ForegroundColor Green
docker run -d \
    --name media-processor-transcription \
    -e LOG_LEVEL=INFO \
    -e DOCKER_ENV=true \
    -e WHISPER_MODEL=base \
    -e DEVICE=cpu \
    -v ${PWD}/uploads:/app/uploads \
    -v ${PWD}/outputs:/app/outputs \
    -v ${PWD}/logs:/app/logs \
    --restart unless-stopped \
    media-processor-transcription:latest

Write-Host "✅ Транскрипция запущена!" -ForegroundColor Green
Write-Host "📋 Для просмотра логов: docker logs -f media-processor-transcription" -ForegroundColor Cyan
