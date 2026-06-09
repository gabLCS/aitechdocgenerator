#!/usr/bin/env bash
set -e

echo "=========================================="
echo "  AutoDocGen - Configuracao Inicial"
echo "=========================================="
echo ""

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Create .env files from examples if not present
if [ ! -f "$ROOT_DIR/backend/.env" ]; then
    echo "[1/4] Criando backend/.env a partir do exemplo..."
    cp "$ROOT_DIR/backend/.env.example" "$ROOT_DIR/backend/.env"
else
    echo "[1/4] backend/.env ja existe, pulando."
fi

if [ ! -f "$ROOT_DIR/frontend/.env" ]; then
    echo "[2/4] Criando frontend/.env a partir do exemplo..."
    cp "$ROOT_DIR/frontend/.env.example" "$ROOT_DIR/frontend/.env"
else
    echo "[2/4] frontend/.env ja existe, pulando."
fi

# Backend dependencies
echo "[3/4] Instalando dependencias do backend..."
cd "$ROOT_DIR/backend"
uv sync

# Frontend dependencies
echo "[4/4] Instalando dependencias do frontend..."
cd "$ROOT_DIR/frontend"
uv sync

echo ""
echo "=========================================="
echo "  Setup concluido!"
echo ""
echo "  Para iniciar:"
echo "    ./start.sh"
echo "=========================================="
