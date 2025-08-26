# Script for starting transcription container
Write-Host "Starting transcription container..." -ForegroundColor Green

# Check if image exists
$imageExists = docker images --format "table {{.Repository}}:{{.Tag}}" | Select-String "transcription-service:latest"
if (-not $imageExists) {
    Write-Host "Image transcription-service:latest not found!" -ForegroundColor Red
    Write-Host "Build image first: ./build.ps1" -ForegroundColor Yellow
    exit 1
}

# Stop existing container
Write-Host "Stopping existing container..." -ForegroundColor Yellow
docker stop transcription-service 2>$null
docker rm transcription-service 2>$null

# Create necessary directories
Write-Host "Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "../../../../../../uploads" | Out-Null
New-Item -ItemType Directory -Force -Path "../../../../../../outputs" | Out-Null
New-Item -ItemType Directory -Force -Path "../../../../../../logs" | Out-Null
New-Item -ItemType Directory -Force -Path "../../../../../models_cache" | Out-Null

# Start container with GPU support
Write-Host "Starting transcription container with GPU support..." -ForegroundColor Green
docker run -d `
    --name transcription-service `
    --gpus all `
    -e LOG_LEVEL=INFO `
    -e DOCKER_ENV=true `
    -e PORT=8002 `
    -e HOST=0.0.0.0 `
    -p 8002:8002 `
    -v "${PWD}/../../../../../../uploads:/app/uploads" `
    -v "${PWD}/../../../../../../outputs:/app/outputs" `
    -v "${PWD}/../../../../../../logs:/app/logs" `
    -v "${PWD}/../../../../../models_cache:/app/app/features/transcription/models_cache" `
    --restart unless-stopped `
    transcription-service:latest

if ($LASTEXITCODE -eq 0) {
    Write-Host "Transcription container started successfully!" -ForegroundColor Green
    Write-Host "Web interface: http://localhost:8002" -ForegroundColor Cyan
    Write-Host "To view logs: docker logs -f transcription-service" -ForegroundColor Cyan
    Write-Host "To check health: ./check.ps1" -ForegroundColor Cyan
    Write-Host "To stop container: ./stop.ps1" -ForegroundColor Cyan
} else {
    Write-Host "Failed to start transcription container!" -ForegroundColor Red
    exit 1
}
