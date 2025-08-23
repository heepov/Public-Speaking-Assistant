# Главный скрипт для сборки и запуска всех контейнеров
Write-Host "🚀 Запуск всех контейнеров одной кнопкой..." -ForegroundColor Green

# Проверяем Docker
Write-Host "🔍 Проверка Docker..." -ForegroundColor Yellow
try {
    docker --version | Out-Null
    Write-Host "✅ Docker найден" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker не найден!" -ForegroundColor Red
    exit 1
}

# Собираем все образы
Write-Host "🔨 Сборка всех образов..." -ForegroundColor Yellow
./scripts/docker-build-microservices.ps1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка при сборке образов!" -ForegroundColor Red
    exit 1
}

# Запускаем все контейнеры
Write-Host "🚀 Запуск всех контейнеров..." -ForegroundColor Yellow
./scripts/docker-run-microservices.ps1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка при запуске контейнеров!" -ForegroundColor Red
    exit 1
}

Write-Host "🎉 Все контейнеры успешно запущены!" -ForegroundColor Green
Write-Host "🌐 Откройте http://localhost:8000 в браузере" -ForegroundColor Cyan
Write-Host "📋 Для остановки: ./scripts/docker-stop.ps1" -ForegroundColor Cyan
