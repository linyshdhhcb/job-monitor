@echo off
chcp 936 >nul
title Job Monitor - Scheduled Mode

echo.
echo ============================================================
echo         Job Monitor - Scheduled Mode (13:00 / 19:00)
echo ============================================================
echo.

cd /d "%~dp0"

if not exist "venv" (
    echo [Error] Please run start.bat first to install dependencies
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

if not exist "data" mkdir data
if not exist "logs" mkdir logs

echo [Start] Starting scheduled monitor...
echo Press Ctrl+C to stop
echo.

python main.py

pause
