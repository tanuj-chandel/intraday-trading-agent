@echo off
title AI Intraday Trading Agent - Autonomous Paper Session
cd /d "%~dp0backend"
echo ======================================================================
echo  AI Intraday Trading Agent - Automated Paper Trading Session (IST)
echo ======================================================================
echo Starting paper session runner at %date% %time%...
venv\Scripts\python.exe run_session.py
echo Session completed at %date% %time% with exit code %errorlevel%.
