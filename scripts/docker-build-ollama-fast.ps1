# Скрипт для быстрой сборки и запуска Ollama Processing с GPU поддержкой
# Модели сохраняются в Docker volume и не удаляются при перезапуске

Write-Host "Быстрая сборка и запуск Ollama Processing с GPU поддержкой" -ForegroundColor Green
Write-Host "=" * 60

# Проверяем Docker
Write-Host "Проверяем Docker..." -ForegroundColor Yellow
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker не установлен!" -ForegroundColor Red
    exit 1
}

# Проверяем NVIDIA Docker
Write-Host "Проверяем NVIDIA Docker..." -ForegroundColor Yellow
try {
    docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi
    Write-Host "NVIDIA Docker работает" -ForegroundColor Green
} catch {
    Write-Host "NVIDIA Docker не работает, будет использоваться CPU" -ForegroundColor Yellow
}

# Останавливаем существующие контейнеры
Write-Host "Останавливаем существующие контейнеры..." -ForegroundColor Yellow
docker-compose -f app/docker/docker-compose.yml stop ollama ollama-processing 2>$null

# Удаляем только образ ollama-processing (не трогаем ollama)
Write-Host "Удаляем старый образ ollama-processing..." -ForegroundColor Yellow
docker rmi ollama-processing:latest 2>$null

# Собираем новый образ
Write-Host "Собираем новый образ ollama-processing..." -ForegroundColor Yellow
docker-compose -f app/docker/docker-compose.yml build ollama-processing

if ($LASTEXITCODE -ne 0) {
    Write-Host "Ошибка при сборке образа!" -ForegroundColor Red
    exit 1
}

# Запускаем сервисы
Write-Host "Запускаем Ollama сервисы..." -ForegroundColor Yellow
docker-compose -f app/docker/docker-compose.yml up -d ollama ollama-processing

if ($LASTEXITCODE -ne 0) {
    Write-Host "Ошибка при запуске сервисов!" -ForegroundColor Red
    exit 1
}

# Ждем запуска
Write-Host "Ждем запуска сервисов..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Проверяем статус
Write-Host "Проверяем статус сервисов..." -ForegroundColor Yellow
docker-compose -f app/docker/docker-compose.yml ps ollama ollama-processing

# Проверяем доступность API
Write-Host "Проверяем доступность API..." -ForegroundColor Yellow
$maxAttempts = 10
$attempt = 1

while ($attempt -le $maxAttempts) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8004/health" -Method GET -TimeoutSec 5
        Write-Host "API доступен!" -ForegroundColor Green
        break
    } catch {
        Write-Host "Попытка $attempt из $maxAttempts: API не доступен..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        $attempt++
    }
}

if ($attempt -gt $maxAttempts) {
    Write-Host "API не доступен после $maxAttempts попыток" -ForegroundColor Red
    Write-Host "Проверяем логи..." -ForegroundColor Yellow
    docker-compose -f app/docker/docker-compose.yml logs ollama-processing --tail=20
}

# Показываем информацию о моделях
Write-Host "Проверяем доступные модели..." -ForegroundColor Yellow
try {
    $models = Invoke-RestMethod -Uri "http://localhost:8004/models" -Method GET -TimeoutSec 10
    Write-Host "Доступные модели: $($models.models -join ', ')" -ForegroundColor Green
} catch {
    Write-Host "Не удалось получить список моделей" -ForegroundColor Yellow
}

Write-Host "=" * 60
Write-Host "Ollama Processing готов к работе!" -ForegroundColor Green
Write-Host "API доступен по адресу: http://localhost:8004" -ForegroundColor Cyan
Write-Host "Документация API: http://localhost:8004/docs" -ForegroundColor Cyan
Write-Host "Ollama сервер: http://localhost:11434" -ForegroundColor Cyan
Write-Host "=" * 60
Write-Host ""
Write-Host "Примеры использования:" -ForegroundColor Yellow
Write-Host "   # Установить модель llama2" -ForegroundColor Gray
Write-Host "   curl -X POST http://localhost:8004/models/install -F 'model_name=llama2'" -ForegroundColor Gray
Write-Host ""
Write-Host "   # Обработать текст с моделью llama2" -ForegroundColor Gray
Write-Host "   curl -X POST http://localhost:8004/process -F 'prompt=Привет, как дела?' -F 'task_id=test123' -F 'model_name=llama2'" -ForegroundColor Gray
Write-Host ""
Write-Host "   # Список доступных моделей" -ForegroundColor Gray
Write-Host "   curl http://localhost:8004/models" -ForegroundColor Gray
