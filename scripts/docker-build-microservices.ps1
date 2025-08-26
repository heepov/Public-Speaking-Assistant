# Скрипт для сборки микросервисных образов
Write-Host "🐳 Сборка микросервисных образов..." -ForegroundColor Green

# Проверяем наличие файлов
$dockerfiles = @("app/docker/Dockerfile", "app/features/video_to_audio/docker/Dockerfile", "app/features/transcription/docker/Dockerfile", "app/features/ollama_processing/docker/Dockerfile")
foreach ($file in $dockerfiles) {
    if (-not (Test-Path $file)) {
        Write-Host "❌ Файл $file не найден!" -ForegroundColor Red
        exit 1
    }
}

# Собираем основной образ
Write-Host "🔨 Сборка основного образа..." -ForegroundColor Yellow
docker build -f app/docker/Dockerfile -t media-processor-main:latest .

# Собираем образ конвертера
Write-Host "🔨 Сборка образа конвертера..." -ForegroundColor Yellow
docker build -f app/features/video_to_audio/docker/Dockerfile -t media-processor-converter:latest .

# Собираем образ транскрипции
Write-Host "🔨 Сборка образа транскрипции..." -ForegroundColor Yellow
docker build -f app/features/transcription/docker/Dockerfile -t media-processor-transcription:latest .

# Собираем образ Ollama Processing
Write-Host "🔨 Сборка образа Ollama Processing..." -ForegroundColor Yellow
docker build -f app/features/ollama_processing/docker/Dockerfile -t ollama-processing:latest .

Write-Host "✅ Все образы собраны успешно!" -ForegroundColor Green
Write-Host "🚀 Для запуска используйте: ./scripts/docker-run-microservices.ps1" -ForegroundColor Cyan
