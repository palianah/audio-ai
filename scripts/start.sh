#!/bin/bash
# Audio AI Editor — macOS launcher
# Uses Docker by default. Pass --local to run without Docker.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MODE="${1:-docker}"

cleanup_docker() {
    echo ""
    echo "🛑 Shutting down Audio AI Editor..."
    cd "$PROJECT_DIR"
    docker compose down 2>/dev/null
    echo "✅ All services stopped."
    exit 0
}

cleanup_local() {
    echo ""
    echo "🛑 Shutting down Audio AI Editor..."
    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null
    [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    pkill -f "vite.*5173" 2>/dev/null || true
    echo "✅ All services stopped."
    exit 0
}

echo "🎵 Audio AI Editor"
echo "==================="

# ─── Docker Mode (default) ───
if [ "$MODE" != "--local" ]; then
    if ! command -v docker &> /dev/null; then
        echo "⚠️  Docker not found — switching to local mode..."
        MODE="--local"
    fi
fi

if [ "$MODE" != "--local" ]; then
    # Auto-start Docker Desktop if daemon is not running
    if ! docker info > /dev/null 2>&1; then
        echo "🐳 Starting Docker Desktop..."
        open -a "Docker Desktop" 2>/dev/null || open -a "Docker" 2>/dev/null
        for i in $(seq 1 60); do
            docker info > /dev/null 2>&1 && break
            sleep 2
        done
        if ! docker info > /dev/null 2>&1; then
            echo "❌ Docker daemon failed to start. Open Docker Desktop manually."
            exit 1
        fi
        echo "✅ Docker Desktop ready"
    fi

    trap cleanup_docker SIGINT SIGTERM EXIT

    echo "🐳 Building & starting containers..."
    cd "$PROJECT_DIR"
    docker compose up --build -d

    # Wait for backend
    echo "⏳ Waiting for services..."
    for i in $(seq 1 60); do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ Backend ready"
            break
        fi
        sleep 1
    done

    # Wait for frontend
    for i in $(seq 1 30); do
        if curl -s http://localhost:5173 > /dev/null 2>&1; then
            echo "✅ Frontend ready"
            break
        fi
        sleep 1
    done

    echo "🌐 Opening browser..."
    open "http://localhost:5173"

    echo ""
    echo "🎵 Audio AI Editor is running! (Docker)"
    echo "   Frontend: http://localhost:5173"
    echo "   Backend:  http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
    echo ""
    echo "Press Ctrl+C to stop all services."
    echo ""

    # Follow logs until Ctrl+C
    docker compose logs -f

    exit 0
fi

# ─── Local Mode (--local) ───
BACKEND_PID=""
FRONTEND_PID=""

trap cleanup_local SIGINT SIGTERM EXIT

# Find Python 3.12/3.11
PYTHON_BIN=""
for p in python3.12 python3.11 python3.13; do
    if command -v "$p" &> /dev/null; then
        PYTHON_BIN="$p"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "❌ Python 3.11/3.12 not found. Install: brew install python@3.12"
    echo "   Or just use Docker mode: ./scripts/start.sh"
    exit 1
fi

echo "🐍 Using $($PYTHON_BIN --version)"

if ! command -v pnpm &> /dev/null; then
    echo "❌ pnpm not found. Install: npm install -g pnpm"
    exit 1
fi

# Setup Python venv
VENV_DIR="$PROJECT_DIR/backend/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating Python virtual environment..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel -q
    "$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/backend/requirements.txt"
fi

# Install frontend deps
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

sleep 3

echo "🌐 Opening browser..."
open "http://localhost:5173"

echo ""
echo "🎵 Audio AI Editor is running! (Local)"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services."
echo ""

wait
