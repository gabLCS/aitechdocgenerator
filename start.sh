#!/usr/bin/env bash
set -e

echo "=========================================="
echo "  AutoDocGen - Iniciando Backend + Frontend"
echo "=========================================="
echo ""

# Start backend in background
echo "[1/2] Iniciando backend (porta 8000)..."
cd "$(dirname "$0")/backend"
uv run uvicorn app.main:app --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Aguardando backend..."
for i in $(seq 1 30); do
  if curl -s http://127.0.0.1:8000 > /dev/null 2>&1; then
    echo "Backend pronto!"
    break
  fi
  sleep 1
done

# Start frontend
echo "[2/2] Iniciando frontend (porta 5001)..."
cd "$(dirname "$0")/frontend"
uv run python app.py &
FRONTEND_PID=$!

echo ""
echo "=========================================="
echo "  Backend:  http://127.0.0.1:8000"
echo "  Frontend: http://127.0.0.1:5001"
echo "=========================================="
echo ""
echo "Pressione Ctrl+C para parar tudo."

# Trap to kill both on Ctrl+C
trap "echo ''; echo 'Parando...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM

wait
