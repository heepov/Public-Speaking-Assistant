# Script for stopping transcription container
Write-Host "Stopping transcription container..." -ForegroundColor Yellow

# Stop container
docker stop transcription-service 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "Transcription container stopped successfully!" -ForegroundColor Green
} else {
    Write-Host "Container was not running or already stopped." -ForegroundColor Yellow
}

# Remove container
Write-Host "Removing transcription container..." -ForegroundColor Yellow
docker rm transcription-service 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "Transcription container removed successfully!" -ForegroundColor Green
} else {
    Write-Host "Container was not found or already removed." -ForegroundColor Yellow
}

Write-Host "To start container again: ./start.ps1" -ForegroundColor Cyan
