# Скрипт для тестирования Ollama Processing Service

Write-Host "🧪 Тестирование Ollama Processing Service..." -ForegroundColor Green

# Проверяем, что контейнер запущен
Write-Host "🔍 Проверка статуса контейнера..." -ForegroundColor Yellow

$containerName = "ollama-processing-container"
$containerStatus = docker ps --filter "name=$containerName" --format "{{.Status}}" 2>$null

if ($containerStatus) {
    Write-Host "✅ Контейнер $containerName запущен: $containerStatus" -ForegroundColor Green
} else {
    Write-Host "❌ Контейнер $containerName не запущен. Запустите: .\scripts\docker-run-ollama.ps1" -ForegroundColor Red
    exit 1
}

# Проверяем, что сервис доступен
Write-Host "🔍 Проверка доступности сервиса..." -ForegroundColor Yellow

try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8004/health" -Method Get -TimeoutSec 10
    Write-Host "✅ Сервис доступен: $($healthResponse.status)" -ForegroundColor Green
} catch {
    Write-Host "❌ Сервис недоступен. Проверьте логи: docker logs $containerName" -ForegroundColor Red
    exit 1
}

# Проверяем статус Ollama
Write-Host "🔍 Проверка статуса Ollama..." -ForegroundColor Yellow

try {
    $ollamaStatus = Invoke-RestMethod -Uri "http://localhost:8004/ollama-status" -Method Get -TimeoutSec 10
    Write-Host "✅ Ollama статус: $($ollamaStatus.status)" -ForegroundColor Green
    Write-Host "📦 Доступные модели: $($ollamaStatus.model_count)" -ForegroundColor Cyan
} catch {
    Write-Host "⚠️  Не удалось получить статус Ollama" -ForegroundColor Yellow
}

# Получаем информацию о модели
Write-Host "🔍 Получение информации о модели..." -ForegroundColor Yellow

try {
    $modelInfo = Invoke-RestMethod -Uri "http://localhost:8004/model-info" -Method Get -TimeoutSec 10
    Write-Host "✅ Информация о модели получена" -ForegroundColor Green
    Write-Host "   Сервис: $($modelInfo.service)" -ForegroundColor Cyan
    Write-Host "   Инициализирован: $($modelInfo.is_initialized)" -ForegroundColor Cyan
    Write-Host "   GPU доступен: $($modelInfo.gpu_available)" -ForegroundColor Cyan
} catch {
    Write-Host "⚠️  Не удалось получить информацию о модели" -ForegroundColor Yellow
}

# Тестируем обработку JSON данных
Write-Host "🧪 Тестирование обработки JSON данных..." -ForegroundColor Yellow

$testData = @{
    "presentation_title" = "Тестовая презентация"
    "speaker" = "Тестовый докладчик"
    "content" = "Это тестовое содержание для проверки работы Ollama сервиса."
}

$testTaskId = "test-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

try {
    $body = @{
        prompt = "Проанализируй эту презентацию и создай краткое резюме"
        data = $testData | ConvertTo-Json -Depth 10
        task_id = $testTaskId
        model_name = "llama2"
        use_openai = $false
    }

    $response = Invoke-RestMethod -Uri "http://localhost:8004/process-json" -Method Post -Body $body -ContentType "application/x-www-form-urlencoded" -TimeoutSec 60
    
    Write-Host "✅ Тест обработки JSON успешен!" -ForegroundColor Green
    Write-Host "   Task ID: $($response.task_id)" -ForegroundColor Cyan
    Write-Host "   Статус: $($response.status)" -ForegroundColor Cyan
    Write-Host "   Модель: $($response.model)" -ForegroundColor Cyan
    Write-Host "   Сервис: $($response.service)" -ForegroundColor Cyan
    
    # Показываем часть результата
    $resultPreview = $response.result.Substring(0, [Math]::Min(200, $response.result.Length))
    Write-Host "   Результат (начало): $resultPreview..." -ForegroundColor White
    
} catch {
    Write-Host "❌ Ошибка при тестировании обработки JSON: $_" -ForegroundColor Red
}

# Тестируем установку модели
Write-Host "🧪 Тестирование установки модели..." -ForegroundColor Yellow

try {
    $body = @{
        model_name = "phi3"
    }

    $response = Invoke-RestMethod -Uri "http://localhost:8004/install-model" -Method Post -Body $body -ContentType "application/x-www-form-urlencoded" -TimeoutSec 120
    
    Write-Host "✅ Тест установки модели успешен!" -ForegroundColor Green
    Write-Host "   Модель: $($response.model_name)" -ForegroundColor Cyan
    Write-Host "   Статус: $($response.status)" -ForegroundColor Cyan
    
} catch {
    Write-Host "⚠️  Ошибка при тестировании установки модели: $_" -ForegroundColor Yellow
}

# Получаем список поддерживаемых форматов
Write-Host "🔍 Получение поддерживаемых форматов..." -ForegroundColor Yellow

try {
    $formats = Invoke-RestMethod -Uri "http://localhost:8004/supported-formats" -Method Get -TimeoutSec 10
    Write-Host "✅ Поддерживаемые форматы:" -ForegroundColor Green
    foreach ($format in $formats.supported_formats) {
        Write-Host "   $($format.extension) - $($format.description)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "⚠️  Не удалось получить список форматов" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Тестирование завершено!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Полезные ссылки:" -ForegroundColor Cyan
Write-Host "   API документация: http://localhost:8004/docs" -ForegroundColor White
Write-Host "   Проверка здоровья: http://localhost:8004/health" -ForegroundColor White
Write-Host "   Статус Ollama: http://localhost:8004/ollama-status" -ForegroundColor White
