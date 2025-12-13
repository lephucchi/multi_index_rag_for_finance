# Development Startup Script (Windows)
# Starts both backend and frontend in separate terminals

Write-Host "🚀 Starting Multi-Index RAG Development Environment..." -ForegroundColor Cyan
Write-Host ""

# Check if backend virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "❌ Virtual environment not found. Creating..." -ForegroundColor Red
    python -m venv venv
}

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Please create one from .env.example" -ForegroundColor Yellow
    exit 1
}

# Check if frontend .env.local exists
if (-not (Test-Path "frontend\.env.local")) {
    Write-Host "⚠️  frontend\.env.local not found. Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item "frontend\.env.example" "frontend\.env.local"
}

# Start backend in new terminal
Write-Host "🔧 Starting Backend API on port 8000..." -ForegroundColor Blue
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\venv\Scripts\Activate.ps1; uvicorn src.api.main:app --reload --port 8000"

# Wait a bit for backend to start
Start-Sleep -Seconds 3

# Start frontend in new terminal
Write-Host "🎨 Starting Frontend on port 3000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; npm run dev"

Write-Host ""
Write-Host "✅ Development environment is starting!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📍 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "📍 Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Close the terminal windows to stop the servers" -ForegroundColor Yellow
