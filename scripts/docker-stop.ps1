# Скрипт для остановки Docker контейнера
Write-Host "⏹️ Остановка сервиса транскрипции..." -ForegroundColor Yellow

# Проверяем, что Docker установлен
try {
    docker --version | Out-Null
} catch {
    Write-Host "❌ Docker не найден!" -ForegroundColor Red
    exit 1
}

# Останавливаем контейнер
Write-Host "🛑 Остановка контейнера..." -ForegroundColor Yellow
docker-compose -f app/docker/docker-compose.yml down

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Сервис остановлен!" -ForegroundColor Green
} else {
    Write-Host "❌ Ошибка при остановке сервиса" -ForegroundColor Red
    exit 1
}
