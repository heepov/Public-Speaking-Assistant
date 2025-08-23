# Скрипт для сборки основного контейнера
Write-Host "🔨 Сборка основного контейнера..." -ForegroundColor Green

# Проверяем наличие файла
if (-not (Test-Path "app/docker/Dockerfile")) {
    Write-Host "❌ Файл app/docker/Dockerfile не найден!" -ForegroundColor Red
    exit 1
}

# Собираем основной образ
Write-Host "🔨 Сборка основного образа..." -ForegroundColor Yellow
docker build -f app/docker/Dockerfile -t media-processor-main:latest .

Write-Host "✅ Основной образ собран успешно!" -ForegroundColor Green
Write-Host "🚀 Для запуска используйте: ./scripts/docker-run-main.ps1" -ForegroundColor Cyan
