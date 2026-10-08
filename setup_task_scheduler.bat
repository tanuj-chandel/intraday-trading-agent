@echo off
title Register Windows Task Scheduler - AI Intraday Trading Agent
echo ======================================================================
echo  Registering Scheduled Task for Autonomous Daily Paper Trading (IST)
echo ======================================================================
echo Task Name: IntradayTradingAgent_DailySession
echo Schedule : Monday to Friday at 09:14 IST (runs 09:15 - 15:15 IST)
echo Target   : "%~dp0run_daily_session.bat"
echo.

schtasks /create /tn "IntradayTradingAgent_DailySession" /tr "\"%~dp0run_daily_session.bat\"" /sc weekly /d MON,TUE,WED,THU,FRI /st 09:14 /f

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Windows Scheduled Task successfully registered!
    echo Daily paper sessions will trigger at 09:14 IST every trading day.
) else (
    echo.
    echo [ERROR] Failed to register task. If needed, run cmd as Administrator.
)
pause
