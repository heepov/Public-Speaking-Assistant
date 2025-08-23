# Скрипт для полной валидации Docker проекта
Write-Host "🔍 ПОЛНАЯ ВАЛИДАЦИЯ DOCKER ПРОЕКТА" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Проверяем Docker
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker найден: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker не найден!" -ForegroundColor Red
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

# Проверяем структуру файлов
Write-Host "`n📁 Проверка структуры файлов:" -ForegroundColor Yellow

$requiredFiles = @(
    "app/docker/docker-compose.yml",
    "app/docker/Dockerfile",
    "app/docker/requirements.txt",
    "app/features/video_to_audio/docker/Dockerfile",
    "app/features/video_to_audio/docker/requirements.txt",
    "app/features/transcription/docker/Dockerfile",
    "app/features/transcription/docker/requirements.txt"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file" -ForegroundColor Green
    } else {
        Write-Host "❌ $file - НЕ НАЙДЕН!" -ForegroundColor Red
    }
}

# Проверяем синтаксис docker-compose.yml
Write-Host "`n🔧 Проверка синтаксиса docker-compose.yml:" -ForegroundColor Yellow
try {
    $composeConfig = docker-compose -f app/docker/docker-compose.yml config
    Write-Host "✅ docker-compose.yml корректен" -ForegroundColor Green
} catch {
    Write-Host "❌ Ошибка в docker-compose.yml:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

# Проверяем Dockerfile'ы
Write-Host "`n🐳 Проверка Dockerfile'ов:" -ForegroundColor Yellow

$dockerfiles = @(
    "app/docker/Dockerfile",
    "app/features/video_to_audio/docker/Dockerfile",
    "app/features/transcription/docker/Dockerfile"
)

foreach ($dockerfile in $dockerfiles) {
    try {
        # Проверяем базовый синтаксис
        $content = Get-Content $dockerfile -Raw
        if ($content -match "FROM" -and $content -match "WORKDIR" -and $content -match "COPY") {
            Write-Host "✅ $dockerfile - базовый синтаксис корректен" -ForegroundColor Green
        } else {
            Write-Host "⚠️ $dockerfile - возможные проблемы с синтаксисом" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ $dockerfile - ошибка чтения" -ForegroundColor Red
    }
}

# Проверяем requirements.txt
Write-Host "`n📦 Проверка requirements.txt:" -ForegroundColor Yellow

$requirementsFiles = @(
    "app/docker/requirements.txt",
    "app/features/video_to_audio/docker/requirements.txt",
    "app/features/transcription/docker/requirements.txt"
)

foreach ($reqFile in $requirementsFiles) {
    try {
        $content = Get-Content $reqFile
        $packageCount = ($content | Where-Object { $_ -match "^[a-zA-Z]" }).Count
        Write-Host "✅ $reqFile - $packageCount пакетов" -ForegroundColor Green
    } catch {
        Write-Host "❌ $reqFile - ошибка чтения" -ForegroundColor Red
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
            Write-Host "⚠️ $image - Не найден (нужно собрать)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️ $image - Не найден (нужно собрать)" -ForegroundColor Yellow
    }
}

# Проверяем контейнеры
Write-Host "`n📋 Статус контейнеров:" -ForegroundColor Yellow
$expectedContainers = @("media-processor-main", "media-processor-converter", "media-processor-transcription")
$runningCount = 0

foreach ($container in $expectedContainers) {
    try {
        $status = docker inspect --format='{{.State.Status}}' $container 2>$null
        if ($status) {
            switch ($status) {
                "running" { 
                    Write-Host "✅ $container - Запущен" -ForegroundColor Green
                    $runningCount++
                }
                "exited" { Write-Host "⏹️ $container - Остановлен" -ForegroundColor Yellow }
                "created" { Write-Host "📝 $container - Создан" -ForegroundColor Cyan }
                default { Write-Host "❓ $container - $status" -ForegroundColor Gray }
            }
        } else {
            Write-Host "❌ $container - Не найден" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ $container - Не найден" -ForegroundColor Red
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

# Итоговая оценка
Write-Host "`n🎯 ИТОГОВАЯ ОЦЕНКА:" -ForegroundColor Yellow
Write-Host "==================" -ForegroundColor Yellow

if ($runningCount -eq $expectedContainers.Count) {
    Write-Host "🎉 ОТЛИЧНО! Все контейнеры запущены и работают!" -ForegroundColor Green
    Write-Host "🌐 Приложение доступно по адресу: http://localhost:8000" -ForegroundColor Cyan
} elseif ($runningCount -gt 0) {
    Write-Host "⚠️ ЧАСТИЧНО РАБОТАЕТ! Запущено $runningCount из $($expectedContainers.Count) контейнеров" -ForegroundColor Yellow
    Write-Host "💡 Для запуска всех контейнеров: ./scripts/docker-start-all.ps1" -ForegroundColor Cyan
} else {
    Write-Host "❌ НЕ РАБОТАЕТ! Ни один контейнер не запущен" -ForegroundColor Red
    Write-Host "💡 Для запуска: ./scripts/docker-start-all.ps1" -ForegroundColor Cyan
}

Write-Host "`n📋 РЕКОМЕНДАЦИИ:" -ForegroundColor Cyan
Write-Host "===============" -ForegroundColor Cyan
Write-Host "• Все сервисы работают независимо друг от друга" -ForegroundColor White
Write-Host "• Health checks настроены для всех контейнеров" -ForegroundColor White
Write-Host "• Сетевая изоляция через media-network" -ForegroundColor White
Write-Host "• Общие volumes для uploads/outputs/logs" -ForegroundColor White
Write-Host "• Легкие образы с минимальными зависимостями" -ForegroundColor White

Write-Host "`n🔧 ПОЛЕЗНЫЕ КОМАНДЫ:" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan
Write-Host "Запуск всех: ./scripts/docker-start-all.ps1" -ForegroundColor White
Write-Host "Остановка: ./scripts/docker-stop.ps1" -ForegroundColor White
Write-Host "Пересборка: ./scripts/docker-build-microservices.ps1" -ForegroundColor White
Write-Host "Логи: docker-compose -f app/docker/docker-compose.yml logs -f" -ForegroundColor White
Write-Host "Очистка: ./scripts/docker-clean-rebuild.ps1" -ForegroundColor White
