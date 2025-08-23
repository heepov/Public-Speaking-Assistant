# Скрипт для запуска основного контейнера
Write-Host "🚀 Запуск основного контейнера..." -ForegroundColor Green

# Проверяем наличие образа
$imageExists = docker images --format "table {{.Repository}}:{{.Tag}}" | Select-String "media-processor-main:latest"
if (-not $imageExists) {
    Write-Host "❌ Образ media-processor-main:latest не найден!" -ForegroundColor Red
    Write-Host "🔨 Сначала соберите образ: ./scripts/docker-build-main.ps1" -ForegroundColor Yellow
    exit 1
}

# Останавливаем существующий контейнер
Write-Host "🛑 Останавливаем существующий контейнер..." -ForegroundColor Yellow
docker stop media-processor-main 2>$null
docker rm media-processor-main 2>$null

# Запускаем основной контейнер
Write-Host "🚀 Запускаем основной контейнер..." -ForegroundColor Green
docker run -d \
    --name media-processor-main \
    -p 8000:8000 \
    -e HOST=0.0.0.0 \
    -e PORT=8000 \
    -e LOG_LEVEL=INFO \
    -e DOCKER_ENV=true \
    -v ${PWD}/uploads:/app/uploads \
    -v ${PWD}/outputs:/app/outputs \
    -v ${PWD}/logs:/app/logs \
    --restart unless-stopped \
    media-processor-main:latest

Write-Host "✅ Основной контейнер запущен!" -ForegroundColor Green
Write-Host "🌐 Откройте http://localhost:8000 в браузере" -ForegroundColor Cyan
Write-Host "📋 Для просмотра логов: docker logs -f media-processor-main" -ForegroundColor Cyan
