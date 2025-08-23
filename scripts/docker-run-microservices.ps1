# Скрипт для запуска микросервисов
Write-Host "🚀 Запуск микросервисов..." -ForegroundColor Green

# Проверяем Docker
try {
    docker --version | Out-Null
    Write-Host "✅ Docker найден" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker не найден!" -ForegroundColor Red
    exit 1
}

# Останавливаем существующие контейнеры
Write-Host "🛑 Останавливаем существующие контейнеры..." -ForegroundColor Yellow
docker-compose -f app/docker/docker-compose.yml down 2>$null

# Запускаем все контейнеры
Write-Host "🚀 Запускаем все контейнеры..." -ForegroundColor Yellow
docker-compose -f app/docker/docker-compose.yml up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка при запуске контейнеров!" -ForegroundColor Red
    exit 1
}

# Ждем немного для запуска
Write-Host "⏳ Ждем запуска контейнеров..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Проверяем статус контейнеров
Write-Host "`n📋 Статус контейнеров:" -ForegroundColor Yellow
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Проверяем health status
Write-Host "`n🏥 Проверка health status:" -ForegroundColor Yellow

$containers = @("media-processor-main", "media-processor-converter", "media-processor-transcription")
$healthyCount = 0

foreach ($container in $containers) {
    try {
        $health = docker inspect --format='{{.State.Health.Status}}' $container 2>$null
        if ($health) {
            switch ($health) {
                "healthy" { 
                    Write-Host "✅ $container - Здоров" -ForegroundColor Green
                    $healthyCount++
                }
                "unhealthy" { Write-Host "❌ $container - Не здоров" -ForegroundColor Red }
                "starting" { Write-Host "🔄 $container - Запускается" -ForegroundColor Yellow }
                default { Write-Host "❓ $container - $health" -ForegroundColor Gray }
            }
        } else {
            Write-Host "⚠️ $container - Health check не настроен" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ $container - Не найден" -ForegroundColor Red
    }
}

Write-Host "`n🎯 Результат:" -ForegroundColor Yellow
if ($healthyCount -eq $containers.Count) {
    Write-Host "🎉 Все контейнеры успешно запущены и здоровы!" -ForegroundColor Green
    Write-Host "🌐 Откройте http://localhost:8000 в браузере" -ForegroundColor Cyan
} else {
    Write-Host "⚠️ Некоторые контейнеры могут быть не готовы" -ForegroundColor Yellow
    Write-Host "📋 Для проверки: ./scripts/check-docker.ps1" -ForegroundColor Cyan
}

Write-Host "📋 Для остановки: ./scripts/docker-stop.ps1" -ForegroundColor Cyan
