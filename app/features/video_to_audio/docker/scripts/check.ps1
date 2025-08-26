# Script for checking video_to_audio container health
Write-Host "Checking video_to_audio container health..." -ForegroundColor Green

# Check container status
Write-Host "Container Status:" -ForegroundColor Yellow
$containerStatus = docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Select-String "video-to-audio"
if ($containerStatus) {
    Write-Host $containerStatus -ForegroundColor Cyan
} else {
    Write-Host "Container video-to-audio not found!" -ForegroundColor Red
    Write-Host "To start container: ./start.ps1" -ForegroundColor Cyan
    exit 1
}

# Check if container is running
$containerRunning = docker ps --format "table {{.Names}}" | Select-String "video-to-audio"
if (-not $containerRunning) {
    Write-Host "Container is not running!" -ForegroundColor Red
    Write-Host "To start container: ./start.ps1" -ForegroundColor Cyan
    exit 1
}

# Check container logs
Write-Host "Recent logs:" -ForegroundColor Yellow
docker logs --tail 10 video-to-audio

# Check health endpoint
Write-Host "Health check:" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8003/health" -Method GET -TimeoutSec 5
    Write-Host "Health check passed!" -ForegroundColor Green
    Write-Host "Status: $($response.status)" -ForegroundColor Cyan
    Write-Host "Service: $($response.service)" -ForegroundColor Cyan
    Write-Host "Timestamp: $($response.timestamp)" -ForegroundColor Cyan
} catch {
    Write-Host "Health check failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    
    # Check if port is listening
    Write-Host "Checking port 8003..." -ForegroundColor Yellow
    $portCheck = netstat -an | Select-String ":8003"
    if ($portCheck) {
        Write-Host "Port 8003 is listening" -ForegroundColor Green
    } else {
        Write-Host "Port 8003 is not listening" -ForegroundColor Red
    }
}

# Check resource usage
Write-Host "Resource usage:" -ForegroundColor Yellow
docker stats video-to-audio --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

Write-Host "Health check completed!" -ForegroundColor Green
