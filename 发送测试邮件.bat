@echo off
chcp 936 >nul
title Send Test Email

echo.
echo ============================================================
echo                   Send Test Email
echo ============================================================
echo.

cd /d "%~dp0"

if exist "venv" (
    call venv\Scripts\activate.bat
) else (
    echo [Error] Please run start.bat first
    pause
    exit /b 1
)

echo [Test] Sending test email...
echo.

python main.py --test

echo.
pause
