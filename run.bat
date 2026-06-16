@echo off
REM Geoffrey Akoo Portfolio - Flask Application Launcher
echo.
echo ===================================================
echo Geoffrey Akoo Portfolio API
echo ===================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo Checking for virtual environment...
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing/updating dependencies...
pip install -q -r requirements.txt

echo.
echo ===================================================
echo Starting Flask Application
echo ===================================================
echo.
echo Server starting on http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

python app.py
pause
