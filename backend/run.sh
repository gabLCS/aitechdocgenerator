#!/usr/bin/env bash
echo "Iniciando o servidor Uvicorn via uv..."
uv run uvicorn app.main:app --port 8000
