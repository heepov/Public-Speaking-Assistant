# Скрипт для полной очистки и пересборки Docker контейнеров
Write-Host "🧹 Полная очистка и пересборка Docker контейнеров..." -ForegroundColor Green

# Проверяем Docker
try {
    docker --version | Out-Null
    Write-Host "✅ Docker найден" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker не найден!" -ForegroundColor Red
    exit 1
}

# Останавливаем и удаляем контейнеры
Write-Host "🛑 Останавливаем контейнеры..." -ForegroundColor Yellow
docker-compose -f app/docker/docker-compose.yml down --remove-orphans 2>$null

# Удаляем контейнеры
Write-Host "🗑️ Удаляем контейнеры..." -ForegroundColor Yellow
docker rm -f media-processor-main media-processor-converter media-processor-transcription 2>$null

# Удаляем образы
Write-Host "🗑️ Удаляем образы..." -ForegroundColor Yellow
docker rmi media-processor-main:latest media-processor-converter:latest media-processor-transcription:latest 2>$null

# Очищаем неиспользуемые ресурсы
Write-Host "🧹 Очищаем неиспользуемые ресурсы..." -ForegroundColor Yellow
docker system prune -f

# Удаляем volumes (опционально)
$removeVolumes = Read-Host "Удалить volumes? (y/N)"
if ($removeVolumes -eq "y" -or $removeVolumes -eq "Y") {
    Write-Host "🗑️ Удаляем volumes..." -ForegroundColor Yellow
    docker volume rm $(docker volume ls -q) 2>$null
}

# Пересобираем образы
Write-Host "🔨 Пересобираем образы..." -ForegroundColor Yellow
./scripts/docker-build-microservices.ps1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка при сборке образов!" -ForegroundColor Red
    exit 1
}

# Запускаем контейнеры
Write-Host "🚀 Запускаем контейнеры..." -ForegroundColor Yellow
./scripts/docker-run-microservices.ps1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка при запуске контейнеров!" -ForegroundColor Red
    exit 1
}

Write-Host "🎉 Полная пересборка завершена!" -ForegroundColor Green
Write-Host "🌐 Откройте http://localhost:8000 в браузере" -ForegroundColor Cyan
Write-Host "📋 Для проверки: ./scripts/check-docker.ps1" -ForegroundColor Cyan
