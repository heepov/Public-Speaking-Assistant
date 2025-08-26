# Скрипт для тестирования Ollama API с различными моделями

Write-Host "🧪 Тестирование Ollama API" -ForegroundColor Green
Write-Host "=" * 50

# Базовый URL API
$baseUrl = "http://localhost:8004"

# Функция для проверки доступности API
function Test-APIHealth {
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/health" -Method GET -TimeoutSec 5
        Write-Host "✅ API доступен" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ API недоступен: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Функция для получения списка моделей
function Get-Models {
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/models" -Method GET -TimeoutSec 10
        Write-Host "📦 Доступные модели: $($response.models -join ', ')" -ForegroundColor Cyan
        return $response.models
    } catch {
        Write-Host "❌ Не удалось получить список моделей: $($_.Exception.Message)" -ForegroundColor Red
        return @()
    }
}

# Функция для установки модели
function Install-Model {
    param([string]$ModelName)
    
    Write-Host "📥 Устанавливаем модель: $ModelName" -ForegroundColor Yellow
    
    try {
        $body = @{
            model_name = $ModelName
        }
        
        $response = Invoke-RestMethod -Uri "$baseUrl/models/install" -Method POST -Form $body -TimeoutSec 300
        Write-Host "✅ Модель $ModelName установлена: $($response.message)" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ Ошибка установки модели $ModelName : $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Функция для обработки текста
function Process-Text {
    param(
        [string]$Prompt,
        [string]$ModelName = "llama2",
        [string]$TaskId = "test-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    )
    
    Write-Host "🔄 Обрабатываем текст с моделью $ModelName..." -ForegroundColor Yellow
    Write-Host "💬 Промпт: $Prompt" -ForegroundColor Gray
    
    try {
        $body = @{
            prompt = $Prompt
            task_id = $TaskId
            model_name = $ModelName
            use_openai = $false
        }
        
        $response = Invoke-RestMethod -Uri "$baseUrl/process" -Method POST -Form $body -TimeoutSec 120
        Write-Host "✅ Обработка завершена" -ForegroundColor Green
        Write-Host "📄 Результат: $($response.result)" -ForegroundColor Cyan
        return $response
    } catch {
        Write-Host "❌ Ошибка обработки: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Основной тест
Write-Host "🔍 Проверяем доступность API..." -ForegroundColor Yellow
if (!(Test-APIHealth)) {
    Write-Host "❌ API недоступен, завершаем тест" -ForegroundColor Red
    exit 1
}

# Получаем список моделей
Write-Host "📦 Получаем список моделей..." -ForegroundColor Yellow
$models = Get-Models

# Тестируем различные модели
$testModels = @("llama2", "llama2:7b", "llama2:13b", "llama2:70b", "llama3", "llama3:8b", "llama3:70b")

foreach ($model in $testModels) {
    Write-Host "=" * 50
    Write-Host "🧪 Тестируем модель: $model" -ForegroundColor Magenta
    
    # Проверяем, установлена ли модель
    if ($models -contains $model) {
        Write-Host "✅ Модель $model уже установлена" -ForegroundColor Green
    } else {
        Write-Host "📥 Модель $model не установлена, устанавливаем..." -ForegroundColor Yellow
        if (!(Install-Model -ModelName $model)) {
            Write-Host "⚠️  Пропускаем модель $model из-за ошибки установки" -ForegroundColor Yellow
            continue
        }
    }
    
    # Тестируем обработку текста
    $testPrompt = "Привет! Расскажи кратко о том, что такое искусственный интеллект."
    $result = Process-Text -Prompt $testPrompt -ModelName $model
    
    if ($result) {
        Write-Host "✅ Тест модели $model прошел успешно" -ForegroundColor Green
    } else {
        Write-Host "❌ Тест модели $model не прошел" -ForegroundColor Red
    }
    
    # Небольшая пауза между тестами
    Start-Sleep -Seconds 2
}

Write-Host "=" * 50
Write-Host "🎉 Тестирование завершено!" -ForegroundColor Green
Write-Host "📊 Итоговый список моделей:" -ForegroundColor Yellow
Get-Models
