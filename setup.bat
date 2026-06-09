@echo off
title AutoDocGen Setup
echo ==========================================
echo   AutoDocGen - Configuracao Inicial
echo ==========================================
echo.

:: Create .env files from examples if not present
if not exist backend\.env (
    echo [1/4] Criando backend\.env a partir do exemplo...
    copy backend\.env.example backend\.env > nul
) else (
    echo [1/4] backend\.env ja existe, pulando.
)

if not exist frontend\.env (
    echo [2/4] Criando frontend\.env a partir do exemplo...
    copy frontend\.env.example frontend\.env > nul
) else (
    echo [2/4] frontend\.env ja existe, pulando.
)

:: Backend dependencies
echo [3/4] Instalando dependencias do backend...
cd backend
uv sync
cd ..

:: Frontend dependencies
echo [4/4] Instalando dependencias do frontend...
cd frontend
uv sync
cd ..

echo.
echo ==========================================
echo   Setup concluido!
echo.
echo   Para iniciar:
echo     Windows: backend\run.bat + frontend\start.bat
echo     macOS/Linux: ./start.sh
echo ==========================================
pause
