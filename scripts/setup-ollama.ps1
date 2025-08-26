# Скрипт для настройки Ollama

Write-Host "🚀 Настройка Ollama для анализа текста..." -ForegroundColor Green

# Проверяем, что Ollama установлен
try {
    ollama --version | Out-Null
    Write-Host "✅ Ollama установлен" -ForegroundColor Green
} catch {
    Write-Host "❌ Ollama не установлен. Установите Ollama с https://ollama.ai" -ForegroundColor Red
    exit 1
}

# Проверяем, что Ollama запущен
Write-Host "🔍 Проверяем статус Ollama..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 10
    Write-Host "✅ Ollama запущен" -ForegroundColor Green
} catch {
    Write-Host "❌ Ollama не запущен. Запустите 'ollama serve' или используйте docker-compose.ollama.yml" -ForegroundColor Red
    exit 1
}

# Устанавливаем модели
Write-Host "📥 Устанавливаем модели..." -ForegroundColor Yellow

$models = @("llama2", "mistral", "codellama", "llama3", "phi3")

foreach ($model in $models) {
    Write-Host "📦 Устанавливаем $model..." -ForegroundColor Cyan
    try {
        ollama pull $model
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $model установлен" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Ошибка установки $model" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️  Ошибка установки $model: $_" -ForegroundColor Yellow
    }
}

Write-Host "✅ Все модели установлены!" -ForegroundColor Green
Write-Host ""

# Показываем доступные модели
Write-Host "📋 Доступные модели:" -ForegroundColor Cyan
try {
    ollama list
} catch {
    Write-Host "⚠️  Не удалось получить список моделей" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Настройка завершена! Теперь вы можете использовать анализ текста в приложении." -ForegroundColor Green
Write-Host ""
Write-Host "💡 Полезные команды:" -ForegroundColor Cyan
Write-Host "   ollama list                    - список моделей" -ForegroundColor White
Write-Host "   ollama run llama2 'Привет'     - тест модели" -ForegroundColor White
Write-Host "   ollama serve                   - запуск сервера" -ForegroundColor White
