# Скрипт для сборки конвертера
Write-Host "🔨 Сборка конвертера..." -ForegroundColor Green

# Проверяем наличие файла
if (-not (Test-Path "app/features/video_to_audio/docker/Dockerfile")) {
    Write-Host "❌ Файл app/features/video_to_audio/docker/Dockerfile не найден!" -ForegroundColor Red
    exit 1
}

# Собираем образ конвертера
Write-Host "🔨 Сборка образа конвертера..." -ForegroundColor Yellow
docker build -f app/features/video_to_audio/docker/Dockerfile -t media-processor-converter:latest .

Write-Host "✅ Образ конвертера собран успешно!" -ForegroundColor Green
Write-Host "🚀 Для запуска используйте: ./scripts/docker-run-converter.ps1" -ForegroundColor Cyan
