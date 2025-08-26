# Script for stopping video_to_audio container
Write-Host "Stopping video_to_audio container..." -ForegroundColor Green

# Check if container is running
$containerRunning = docker ps --format "table {{.Names}}" | Select-String "video-to-audio"
if ($containerRunning) {
    Write-Host "Stopping video-to-audio container..." -ForegroundColor Yellow
    docker stop video-to-audio
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Video to audio container stopped successfully!" -ForegroundColor Green
    } else {
        Write-Host "Failed to stop video_to_audio container!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Video to audio container is not running" -ForegroundColor Yellow
}

# Remove container
Write-Host "Removing video-to-audio container..." -ForegroundColor Yellow
docker rm video-to-audio 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "Video to audio container removed successfully!" -ForegroundColor Green
} else {
    Write-Host "Container was already removed or didn't exist" -ForegroundColor Yellow
}

Write-Host "To start container again: ./start.ps1" -ForegroundColor Cyan
