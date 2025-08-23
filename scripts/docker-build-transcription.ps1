# Скрипт для сборки транскрипции
Write-Host "🔨 Сборка транскрипции..." -ForegroundColor Green

# Проверяем наличие файла
if (-not (Test-Path "app/features/transcription/docker/Dockerfile")) {
    Write-Host "❌ Файл app/features/transcription/docker/Dockerfile не найден!" -ForegroundColor Red
    exit 1
}

# Собираем образ транскрипции
Write-Host "🔨 Сборка образа транскрипции..." -ForegroundColor Yellow
docker build -f app/features/transcription/docker/Dockerfile -t media-processor-transcription:latest .

Write-Host "✅ Образ транскрипции собран успешно!" -ForegroundColor Green
Write-Host "🚀 Для запуска используйте: ./scripts/docker-run-transcription.ps1" -ForegroundColor Cyan
