#!/bin/bash

# Development Startup Script
# Starts both backend and frontend in parallel

set -e

echo "🚀 Starting Multi-Index RAG Development Environment..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if backend virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating..."
    python -m venv venv
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Please create one from .env.example"
    exit 1
fi

# Check if frontend .env.local exists
if [ ! -f "frontend/.env.local" ]; then
    echo "⚠️  frontend/.env.local not found. Creating from .env.example..."
    cp frontend/.env.example frontend/.env.local
fi

# Start backend in background
echo -e "${BLUE}🔧 Starting Backend API on port 8000...${NC}"
source venv/bin/activate
uvicorn src.api.main:app --reload --port 8000 &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Start frontend
echo -e "${GREEN}🎨 Starting Frontend on port 3000...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Development environment is ready!"
echo ""
echo "📍 Backend API: http://localhost:8000"
echo "📍 API Docs: http://localhost:8000/docs"
echo "📍 Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
