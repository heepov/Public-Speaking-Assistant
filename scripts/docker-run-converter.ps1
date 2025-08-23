# Скрипт для запуска конвертера
Write-Host "🚀 Запуск конвертера..." -ForegroundColor Green

# Проверяем наличие образа
$imageExists = docker images --format "table {{.Repository}}:{{.Tag}}" | Select-String "media-processor-converter:latest"
if (-not $imageExists) {
    Write-Host "❌ Образ media-processor-converter:latest не найден!" -ForegroundColor Red
    Write-Host "🔨 Сначала соберите образ: ./scripts/docker-build-converter.ps1" -ForegroundColor Yellow
    exit 1
}

# Останавливаем существующий контейнер
Write-Host "🛑 Останавливаем существующий контейнер..." -ForegroundColor Yellow
docker stop media-processor-converter 2>$null
docker rm media-processor-converter 2>$null

# Запускаем конвертер
Write-Host "🚀 Запускаем конвертер..." -ForegroundColor Green
docker run -d \
    --name media-processor-converter \
    -e LOG_LEVEL=INFO \
    -e DOCKER_ENV=true \
    -v ${PWD}/uploads:/app/uploads \
    -v ${PWD}/outputs:/app/outputs \
    -v ${PWD}/logs:/app/logs \
    --restart unless-stopped \
    media-processor-converter:latest

Write-Host "✅ Конвертер запущен!" -ForegroundColor Green
Write-Host "📋 Для просмотра логов: docker logs -f media-processor-converter" -ForegroundColor Cyan
