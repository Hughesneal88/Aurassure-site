# Aurassure Site Startup Script
# This script starts both the backend and frontend servers

Write-Host "Starting Aurassure Data Download Site..." -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  Warning: .env file not found!" -ForegroundColor Yellow
    Write-Host "Please create a .env file with your Aurassure credentials."
    Write-Host "See .env.example for the required format."
    exit 1
}

# Start backend
Write-Host "🐍 Starting Flask backend..." -ForegroundColor Green
Set-Location backend
$backendProcess = Start-Process -FilePath "python" -ArgumentList "app.py" -PassThru -NoNewWindow
Set-Location ..

# Wait a moment for backend to start
Start-Sleep -Seconds 2

# Start frontend
Write-Host "⚛️  Starting React frontend..." -ForegroundColor Green
Set-Location frontend
$frontendProcess = Start-Process -FilePath "npm" -ArgumentList "start" -PassThru -NoNewWindow
Set-Location ..

Write-Host ""
Write-Host "✅ Both servers are starting!" -ForegroundColor Green
Write-Host "Backend PID: $($backendProcess.Id)"
Write-Host "Frontend PID: $($frontendProcess.Id)"
Write-Host ""
Write-Host "Backend running at: http://localhost:5000"
Write-Host "Frontend running at: http://localhost:3000"
Write-Host ""
Write-Host "Press Ctrl+C to stop both servers" -ForegroundColor Yellow

# Handle Ctrl+C to clean up processes
$cleanup = {
    Write-Host "`nStopping servers..." -ForegroundColor Yellow
    if ($backendProcess -and !$backendProcess.HasExited) {
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($frontendProcess -and !$frontendProcess.HasExited) {
        Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    exit
}

# Register event handler for Ctrl+C
[Console]::TreatControlCAsInput = $false
try {
    Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action $cleanup | Out-Null
    
    # Wait for processes to exit
    while ($true) {
        if ($backendProcess.HasExited -or $frontendProcess.HasExited) {
            Write-Host "One of the servers has stopped. Cleaning up..." -ForegroundColor Yellow
            & $cleanup
        }
        Start-Sleep -Seconds 1
    }
}
finally {
    & $cleanup
}
