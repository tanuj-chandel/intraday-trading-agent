@echo off
title AI Intraday Trading Agent — Indian Equities
color 0B
cls
echo ======================================================================
echo             AI INTRADAY TRADING AGENT (NSE / BSE)
echo ======================================================================
echo.
cd /d "%~dp0"

echo [1/2] Starting Backend API (FastAPI) on Port 8000...
start "Trading Agent - Backend (Port 8000)" /D "%~dp0backend" cmd /k "venv\Scripts\activate && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend Terminal (Next.js) on Port 3001...
start "Trading Agent - Frontend (Port 3001)" /D "%~dp0frontend" cmd /k "npm run dev"

timeout /t 5 /nobreak >nul

echo [*] Opening Live Trading Terminal at http://localhost:3001...
start http://localhost:3001

echo.
echo ======================================================================
echo   [OK] Trading Agent is live!
echo   Frontend UI:  http://localhost:3001
echo   Backend Docs: http://localhost:8000/docs
echo   Keep both terminal windows open while using.
echo ======================================================================
timeout /t 5 >nul