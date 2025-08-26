# Script for starting video_to_audio container
Write-Host "Starting video_to_audio container..." -ForegroundColor Green

# Check if image exists
$imageExists = docker images --format "table {{.Repository}}:{{.Tag}}" | Select-String "video-to-audio:latest"
if (-not $imageExists) {
    Write-Host "Image video-to-audio:latest not found!" -ForegroundColor Red
    Write-Host "Build image first: ./build.ps1" -ForegroundColor Yellow
    exit 1
}

# Stop existing container
Write-Host "Stopping existing container..." -ForegroundColor Yellow
docker stop video-to-audio 2>$null
docker rm video-to-audio 2>$null

# Create necessary directories
Write-Host "Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "../../../../../../uploads" | Out-Null
New-Item -ItemType Directory -Force -Path "../../../../../../outputs" | Out-Null
New-Item -ItemType Directory -Force -Path "../../../../../../logs" | Out-Null

# Start container
Write-Host "Starting video_to_audio container..." -ForegroundColor Green
docker run -d `
    --name video-to-audio `
    -e LOG_LEVEL=INFO `
    -e DOCKER_ENV=true `
    -e PORT=8003 `
    -e HOST=0.0.0.0 `
    -p 8003:8003 `
    -v "${PWD}/../../../../../../uploads:/app/uploads" `
    -v "${PWD}/../../../../../../outputs:/app/outputs" `
    -v "${PWD}/../../../../../../logs:/app/logs" `
    --restart unless-stopped `
    video-to-audio:latest

if ($LASTEXITCODE -eq 0) {
    Write-Host "Video to audio container started successfully!" -ForegroundColor Green
    Write-Host "To view logs: docker logs -f video-to-audio" -ForegroundColor Cyan
    Write-Host "To check health: ./check.ps1" -ForegroundColor Cyan
    Write-Host "To stop container: ./stop.ps1" -ForegroundColor Cyan
} else {
    Write-Host "Failed to start video_to_audio container!" -ForegroundColor Red
    exit 1
}
