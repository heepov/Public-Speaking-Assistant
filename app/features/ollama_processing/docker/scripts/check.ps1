# Script for checking ollama processing container status
Write-Host "Checking ollama processing container status..." -ForegroundColor Green

# Check if container exists and is running
$containerStatus = docker ps -a --format "table {{.Names}}\t{{.Status}}" | Select-String "ollama-processing-service"

if ($containerStatus) {
    Write-Host "Container status:" -ForegroundColor Yellow
    Write-Host $containerStatus -ForegroundColor Cyan
    
    # Check if container is running
    $isRunning = docker ps --format "table {{.Names}}" | Select-String "ollama-processing-service"
    
    if ($isRunning) {
        Write-Host "✅ Container is running!" -ForegroundColor Green
        
        # Check health endpoint
        Write-Host "Checking health endpoint..." -ForegroundColor Yellow
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8004/health" -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ Health endpoint is responding!" -ForegroundColor Green
                Write-Host "Response: $($response.Content)" -ForegroundColor Cyan
            } else {
                Write-Host "⚠️  Health endpoint returned status: $($response.StatusCode)" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "❌ Health endpoint is not responding: $($_.Exception.Message)" -ForegroundColor Red
        }
        
        # Show recent logs
        Write-Host "Recent logs:" -ForegroundColor Yellow
        docker logs --tail 10 ollama-processing-service
        
    } else {
        Write-Host "❌ Container is not running!" -ForegroundColor Red
        Write-Host "To start container: ./start.ps1" -ForegroundColor Cyan
    }
} else {
    Write-Host "❌ Container not found!" -ForegroundColor Red
    Write-Host "To build and start container: ./build.ps1" -ForegroundColor Cyan
}
