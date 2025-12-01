@echo off
chcp 936 >nul
title Job Monitor System

echo.
echo ============================================================
echo            Job Monitor System - Starting
echo ============================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found, please install Python 3.8+
    echo.
    echo Download: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: Change to script directory
cd /d "%~dp0"

:: Check and create venv
if not exist "venv" (
    echo [Info] First run, creating virtual environment...
    python -m venv venv
    
    echo [Info] Installing dependencies, please wait...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    echo.
    echo [Done] Dependencies installed!
    echo.
) else (
    call venv\Scripts\activate.bat
)

:: Create directories
if not exist "data" mkdir data
if not exist "logs" mkdir logs

echo [Start] Running job check...
echo.

:: Run once (test mode)
python main.py --once

echo.
echo ============================================================
echo            Check completed!
echo ============================================================
pause
