# Скрипт для сборки Docker образа Ollama Processing Service

Write-Host "🔨 Сборка Docker образа Ollama Processing Service..." -ForegroundColor Green

# Проверяем, что Docker запущен
try {
    docker version | Out-Null
    Write-Host "✅ Docker доступен" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker не запущен или не установлен" -ForegroundColor Red
    exit 1
}

# Переходим в корневую директорию проекта
Set-Location $PSScriptRoot\..

# Проверяем наличие requirements.txt для Ollama
$ollamaRequirementsPath = "app\features\ollama_processing\docker\requirements.txt"
if (-not (Test-Path $ollamaRequirementsPath)) {
    Write-Host "❌ Файл requirements.txt не найден: $ollamaRequirementsPath" -ForegroundColor Red
    exit 1
}
Write-Host "✅ requirements.txt найден: $ollamaRequirementsPath" -ForegroundColor Green

# Собираем Docker образ
Write-Host "🔨 Сборка образа ollama-processing..." -ForegroundColor Yellow

try {
    docker build -f app\features\ollama_processing\docker\Dockerfile -t ollama-processing .
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Образ ollama-processing успешно собран" -ForegroundColor Green
        
        # Показываем информацию об образе
        Write-Host "📊 Информация об образе:" -ForegroundColor Cyan
        docker images ollama-processing
    } else {
        Write-Host "❌ Ошибка при сборке образа" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Ошибка при сборке Docker образа: $_" -ForegroundColor Red
    exit 1
}

Write-Host "🎉 Сборка завершена успешно!" -ForegroundColor Green
