# Script for building video_to_audio container
Write-Host "Building video_to_audio container..." -ForegroundColor Green

# Check if Dockerfile exists
if (-not (Test-Path "../Dockerfile")) {
    Write-Host "Dockerfile not found!" -ForegroundColor Red
    exit 1
}

# Check if requirements.txt exists
if (-not (Test-Path "../requirements.txt")) {
    Write-Host "requirements.txt not found!" -ForegroundColor Red
    exit 1
}

# Stop and remove existing container
Write-Host "Stopping existing container..." -ForegroundColor Yellow
docker stop video-to-audio 2>$null
docker rm video-to-audio 2>$null

# Remove existing image
Write-Host "Removing existing image..." -ForegroundColor Yellow
docker rmi video-to-audio:latest 2>$null

# Build image
Write-Host "Building video_to_audio image..." -ForegroundColor Yellow
docker build -f ../Dockerfile -t video-to-audio:latest ../../../../..

if ($LASTEXITCODE -eq 0) {
    Write-Host "Video to audio image built successfully!" -ForegroundColor Green
    Write-Host "To start container: ./start.ps1" -ForegroundColor Cyan
} else {
    Write-Host "Failed to build video_to_audio image!" -ForegroundColor Red
    exit 1
}
