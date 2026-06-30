#!/bin/bash
# Audio AI Editor — macOS launcher
# Starts backend + frontend, opens browser, kills all on exit.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo ""
    echo "🛑 Shutting down Audio AI Editor..."
    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null
    [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null
    # Kill any remaining child processes
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    pkill -f "vite.*5173" 2>/dev/null || true
    echo "✅ All services stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

echo "🎵 Audio AI Editor"
echo "==================="

# Check dependencies
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 not found. Please install Python 3.11+"
    exit 1
fi

if ! command -v pnpm &> /dev/null; then
    echo "❌ pnpm not found. Install: npm install -g pnpm"
    exit 1
fi

# Setup Python venv if needed
VENV_DIR="$PROJECT_DIR/backend/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install -q -r "$PROJECT_DIR/backend/requirements.txt"
fi

# Install frontend deps if needed
if [ ! -d "$PROJECT_DIR/frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd "$PROJECT_DIR/frontend"
    pnpm install
fi

# Start Backend
echo "🐍 Starting backend (port 8000)..."
cd "$PROJECT_DIR/backend"
"$VENV_DIR/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to be ready
echo "⏳ Waiting for backend..."
for i in $(seq 1 30); do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend ready"
        break
    fi
    sleep 1
done

# Start Frontend
echo "⚛️  Starting frontend (port 5173)..."
cd "$PROJECT_DIR/frontend"
pnpm run dev &
FRONTEND_PID=$!

# Wait for frontend
sleep 3

# Open browser
echo "🌐 Opening browser..."
open "http://localhost:5173"

echo ""
echo "🎵 Audio AI Editor is running!"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services."
echo ""

# Wait for processes
wait
