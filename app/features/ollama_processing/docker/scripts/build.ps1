# Script for building ollama processing container
Write-Host "Building ollama processing container..." -ForegroundColor Green

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
docker stop ollama-processing-service 2>$null
docker rm ollama-processing-service 2>$null

# Remove existing image
Write-Host "Removing existing image..." -ForegroundColor Yellow
docker rmi ollama-processing-service:latest 2>$null

# Build image
Write-Host "Building ollama processing image..." -ForegroundColor Yellow
docker build -f ../Dockerfile -t ollama-processing-service:latest ../../../../..

if ($LASTEXITCODE -eq 0) {
    Write-Host "Ollama processing image built successfully!" -ForegroundColor Green
    Write-Host "To start container: ./start.ps1" -ForegroundColor Cyan
} else {
    Write-Host "Failed to build ollama processing image!" -ForegroundColor Red
    exit 1
}
