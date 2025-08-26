# Script for starting ollama processing container
Write-Host "Starting ollama processing container..." -ForegroundColor Green

# Check if image exists
$imageExists = docker images --format "table {{.Repository}}:{{.Tag}}" | Select-String "ollama-processing-service:latest"
if (-not $imageExists) {
    Write-Host "Image ollama-processing-service:latest not found!" -ForegroundColor Red
    Write-Host "Build image first: ./build.ps1" -ForegroundColor Yellow
    exit 1
}

# Stop existing container
Write-Host "Stopping existing container..." -ForegroundColor Yellow
docker stop ollama-processing-service 2>$null
docker rm ollama-processing-service 2>$null

# Create necessary directories
Write-Host "Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "../../../../../../uploads" | Out-Null
New-Item -ItemType Directory -Force -Path "../../../../../../outputs" | Out-Null
New-Item -ItemType Directory -Force -Path "../../../../../../logs" | Out-Null
New-Item -ItemType Directory -Force -Path "../../../../../models_cache" | Out-Null

# Start container with GPU support
Write-Host "Starting ollama processing container with GPU support..." -ForegroundColor Green
docker run -d `
    --name ollama-processing-service `
    --gpus all `
    -e LOG_LEVEL=INFO `
    -e DOCKER_ENV=true `
    -e PORT=8004 `
    -e HOST=0.0.0.0 `
    -e OLLAMA_HOST=localhost:11434 `
    -e CUDA_VISIBLE_DEVICES=0 `
    -e OLLAMA_ORIGINS=* `
    -p 8004:8004 `
    -v "${PWD}/../../../../../../uploads:/app/uploads" `
    -v "${PWD}/../../../../../../outputs:/app/outputs" `
    -v "${PWD}/../../../../../../logs:/app/logs" `
    -v "${PWD}/../../../../../models_cache:/app/app/features/ollama_processing/models_cache" `
    --restart unless-stopped `
    ollama-processing-service:latest

if ($LASTEXITCODE -eq 0) {
    Write-Host "Ollama processing container started successfully!" -ForegroundColor Green
    Write-Host "Web interface: http://localhost:8004" -ForegroundColor Cyan
    Write-Host "To view logs: docker logs -f ollama-processing-service" -ForegroundColor Cyan
    Write-Host "To check health: ./check.ps1" -ForegroundColor Cyan
    Write-Host "To stop container: ./stop.ps1" -ForegroundColor Cyan
} else {
    Write-Host "Failed to start ollama processing container!" -ForegroundColor Red
    exit 1
}
