# Скрипт для остановки Docker контейнера Ollama Processing Service

Write-Host "🛑 Остановка Docker контейнера Ollama Processing Service..." -ForegroundColor Green

# Проверяем, что Docker запущен
try {
    docker version | Out-Null
    Write-Host "✅ Docker доступен" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker не запущен или не установлен" -ForegroundColor Red
    exit 1
}

# Останавливаем контейнер
$containerName = "ollama-processing-container"
$existingContainer = docker ps -a --filter "name=$containerName" --format "{{.Names}}"

if ($existingContainer) {
    Write-Host "🛑 Остановка контейнера $containerName..." -ForegroundColor Yellow
    
    # Останавливаем контейнер
    docker stop $containerName
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Контейнер $containerName остановлен" -ForegroundColor Green
        
        # Удаляем контейнер
        Write-Host "🗑️ Удаление контейнера $containerName..." -ForegroundColor Yellow
        docker rm $containerName
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Контейнер $containerName удален" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Контейнер $containerName не был удален" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ Ошибка при остановке контейнера $containerName" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "ℹ️ Контейнер $containerName не найден" -ForegroundColor Cyan
}

Write-Host "🎉 Остановка завершена!" -ForegroundColor Green
