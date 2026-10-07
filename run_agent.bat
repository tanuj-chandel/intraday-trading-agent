@echo off
title AI Intraday Trading Agent - Indian Market
echo ===================================================
echo   Starting AI Intraday Trading Agent (Local Host)
echo ===================================================
echo.

echo [1/2] Starting Backend API (FastAPI) on Port 8000...
start "Trading Agent - Backend (Port 8000)" /D "%~dp0backend" cmd /k "venv\Scripts\activate && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend Dashboard on Port 3000...
start "Trading Agent - Frontend (Port 3000)" /D "%~dp0frontend" cmd /k "npm run dev"

timeout /t 5 /nobreak >nul

echo Opening browser at http://localhost:3000...
start http://localhost:3000

echo.
echo ===================================================
echo   Both services are running in dedicated windows!
echo   Keep those two terminal windows open while using.
echo ===================================================