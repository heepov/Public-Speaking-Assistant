# Скрипт для проверки состояния Docker контейнеров
Write-Host "🔍 Проверка состояния Docker контейнеров..." -ForegroundColor Green

# Проверяем Docker
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker найден: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker не найден!" -ForegroundColor Red
    Write-Host "💡 Установите Docker Desktop с https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    exit 1
}

# Проверяем Docker Compose
try {
    $composeVersion = docker-compose --version
    Write-Host "✅ Docker Compose найден: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose не найден!" -ForegroundColor Red
    exit 1
}

# Проверяем запущенные контейнеры
Write-Host "`n📋 Статус контейнеров:" -ForegroundColor Yellow
$containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
if ($containers) {
    Write-Host $containers
} else {
    Write-Host "⚠️ Нет запущенных контейнеров" -ForegroundColor Yellow
}

# Проверяем все контейнеры (включая остановленные)
Write-Host "`n📋 Все контейнеры (включая остановленные):" -ForegroundColor Yellow
$allContainers = docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
Write-Host $allContainers

# Проверяем health status
Write-Host "`n🏥 Проверка health status:" -ForegroundColor Yellow

$expectedContainers = @("media-processor-main", "media-processor-converter", "media-processor-transcription")
$healthyCount = 0

foreach ($container in $expectedContainers) {
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
            Write-Host "⚠️ $container - Health check не настроен или контейнер не запущен" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ $container - Не найден" -ForegroundColor Red
    }
}

# Проверяем логи последних ошибок
Write-Host "`n📝 Последние ошибки в логах:" -ForegroundColor Yellow
foreach ($container in $expectedContainers) {
    try {
        $logs = docker logs --tail=5 $container 2>$null
        if ($logs -match "ERROR|Exception|Error|Failed") {
            Write-Host "⚠️ $container" -ForegroundColor Yellow
            $logs | Select-String "ERROR|Exception|Error|Failed" | ForEach-Object {
                Write-Host "   $_" -ForegroundColor Red
            }
        }
    } catch {
        # Контейнер не найден или не запущен
    }
}

# Проверяем порты
Write-Host "`n🌐 Проверка портов:" -ForegroundColor Yellow
$ports = @(8000, 8001, 8002)
foreach ($port in $ports) {
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $port -InformationLevel Quiet -WarningAction SilentlyContinue
        if ($connection) {
            Write-Host "✅ Порт $port - Открыт" -ForegroundColor Green
        } else {
            Write-Host "❌ Порт $port - Закрыт" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Порт $port - Недоступен" -ForegroundColor Red
    }
}

# Проверяем образы
Write-Host "`n🐳 Проверка образов:" -ForegroundColor Yellow
$expectedImages = @("media-processor-main:latest", "media-processor-converter:latest", "media-processor-transcription:latest")
foreach ($image in $expectedImages) {
    try {
        $imageInfo = docker images $image --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
        if ($imageInfo -and $imageInfo -notmatch "REPOSITORY") {
            Write-Host "✅ $image - Найден" -ForegroundColor Green
        } else {
            Write-Host "❌ $image - Не найден" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ $image - Не найден" -ForegroundColor Red
    }
}

Write-Host "`n🎯 Результат проверки:" -ForegroundColor Yellow
if ($healthyCount -eq $expectedContainers.Count) {
    Write-Host "🎉 Все контейнеры здоровы и работают!" -ForegroundColor Green
    Write-Host "🌐 Откройте http://localhost:8000 в браузере" -ForegroundColor Cyan
} else {
    Write-Host "⚠️ Некоторые контейнеры могут быть не готовы" -ForegroundColor Yellow
    Write-Host "💡 Для перезапуска: ./scripts/docker-start-all.ps1" -ForegroundColor Cyan
}

Write-Host "`n📋 Полезные команды:" -ForegroundColor Cyan
Write-Host "   Запуск всех: ./scripts/docker-start-all.ps1" -ForegroundColor White
Write-Host "   Остановка: ./scripts/docker-stop.ps1" -ForegroundColor White
Write-Host "   Логи: docker-compose -f app/docker/docker-compose.yml logs -f" -ForegroundColor White
Write-Host "   Пересборка: ./scripts/docker-build-microservices.ps1" -ForegroundColor White
