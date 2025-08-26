# Script for stopping ollama processing container
Write-Host "Stopping ollama processing container..." -ForegroundColor Green

# Stop and remove container
Write-Host "Stopping container..." -ForegroundColor Yellow
docker stop ollama-processing-service 2>$null
docker rm ollama-processing-service 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "Ollama processing container stopped successfully!" -ForegroundColor Green
} else {
    Write-Host "Container was not running or already stopped." -ForegroundColor Yellow
}
