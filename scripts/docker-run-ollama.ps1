# Скрипт для запуска Docker контейнера Ollama Processing Service

Write-Host "🚀 Запуск Docker контейнера Ollama Processing Service..." -ForegroundColor Green

# Проверяем, что Docker запущен
try {
    docker version | Out-Null
    Write-Host "✅ Docker доступен" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker не запущен или не установлен" -ForegroundColor Red
    exit 1
}

# Проверяем, что образ существует
$imageExists = docker images ollama-processing --format "table {{.Repository}}" | Select-String "ollama-processing"
if (-not $imageExists) {
    Write-Host "❌ Образ ollama-processing не найден. Сначала выполните сборку: .\scripts\docker-build-ollama.ps1" -ForegroundColor Red
    exit 1
}

# Останавливаем существующий контейнер если запущен
$containerName = "ollama-processing-container"
$existingContainer = docker ps -a --filter "name=$containerName" --format "{{.Names}}"
if ($existingContainer) {
    Write-Host "🛑 Остановка существующего контейнера..." -ForegroundColor Yellow
    docker stop $containerName
    docker rm $containerName
}

# Создаем необходимые директории
$directories = @("uploads", "outputs", "logs")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "📁 Создана директория: $dir" -ForegroundColor Yellow
    }
}

# Запускаем контейнер
Write-Host "🚀 Запуск контейнера ollama-processing..." -ForegroundColor Yellow

try {
    docker run -d `
        --name $containerName `
        --restart unless-stopped `
        -p 8004:8004 `
        -v "${PWD}/uploads:/app/uploads" `
        -v "${PWD}/outputs:/app/outputs" `
        -v "${PWD}/logs:/app/logs" `
        -e OLLAMA_HOST=localhost:11434 `
        -e PORT=8004 `
        -e HOST=0.0.0.0 `
        ollama-processing
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Контейнер ollama-processing успешно запущен" -ForegroundColor Green
        
        # Ждем немного для инициализации
        Write-Host "⏳ Ожидание инициализации сервиса..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        
        # Проверяем статус контейнера
        $containerStatus = docker ps --filter "name=$containerName" --format "{{.Status}}"
        Write-Host "📊 Статус контейнера: $containerStatus" -ForegroundColor Cyan
        
        # Показываем логи
        Write-Host "📋 Последние логи контейнера:" -ForegroundColor Cyan
        docker logs --tail 20 $containerName
        
        Write-Host ""
        Write-Host "🌐 Сервис доступен по адресу: http://localhost:8004" -ForegroundColor Green
        Write-Host "📚 API документация: http://localhost:8004/docs" -ForegroundColor Green
        Write-Host "🔍 Проверка здоровья: http://localhost:8004/health" -ForegroundColor Green
        
    } else {
        Write-Host "❌ Ошибка при запуске контейнера" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Ошибка при запуске Docker контейнера: $_" -ForegroundColor Red
    exit 1
}

Write-Host "🎉 Запуск завершен успешно!" -ForegroundColor Green
