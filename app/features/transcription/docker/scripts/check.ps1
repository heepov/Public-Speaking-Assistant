# Script for checking transcription container status
Write-Host "Checking transcription container status..." -ForegroundColor Green

# Check if container is running
$containerRunning = docker ps --format "table {{.Names}}" | Select-String "transcription-service"
if ($containerRunning) {
    Write-Host "✅ Transcription container is running" -ForegroundColor Green
    
    # Show container details
    Write-Host "`nContainer details:" -ForegroundColor Cyan
    docker ps --filter "name=transcription-service" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    # Check health endpoint
    Write-Host "`nChecking health endpoint..." -ForegroundColor Cyan
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8002/health" -Method GET -TimeoutSec 10
        Write-Host "✅ Health check passed" -ForegroundColor Green
        Write-Host "Service status: $($response.status)" -ForegroundColor Green
    } catch {
        Write-Host "❌ Health check failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Show logs
    Write-Host "`nRecent logs:" -ForegroundColor Cyan
    docker logs --tail 10 transcription-service
    
} else {
    Write-Host "❌ Transcription container is not running" -ForegroundColor Red
    
    # Check if container exists but is stopped
    $containerExists = docker ps -a --format "table {{.Names}}" | Select-String "transcription-service"
    if ($containerExists) {
        Write-Host "Container exists but is stopped. To start: ./start.ps1" -ForegroundColor Yellow
    } else {
        Write-Host "Container does not exist. To build and start: ./build.ps1 && ./start.ps1" -ForegroundColor Yellow
    }
}
