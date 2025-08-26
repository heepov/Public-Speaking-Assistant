# Script for building transcription container
Write-Host "Building transcription container..." -ForegroundColor Green

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
docker stop transcription-service 2>$null
docker rm transcription-service 2>$null

# Remove existing image
Write-Host "Removing existing image..." -ForegroundColor Yellow
docker rmi transcription-service:latest 2>$null

# Build image
Write-Host "Building transcription image..." -ForegroundColor Yellow
docker build -f ../Dockerfile -t transcription-service:latest ../../../../..

if ($LASTEXITCODE -eq 0) {
    Write-Host "Transcription image built successfully!" -ForegroundColor Green
    Write-Host "To start container: ./start.ps1" -ForegroundColor Cyan
} else {
    Write-Host "Failed to build transcription image!" -ForegroundColor Red
    exit 1
}
