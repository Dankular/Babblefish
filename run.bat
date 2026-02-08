@echo off
REM BabbleFish startup script for Windows

echo ================================
echo  BabbleFish Translation Service
echo ================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo Checking dependencies...
pip install -r requirements.txt --quiet
echo.

REM Check if models are set up
if not exist "models\nllb-ct2" (
    echo.
    echo WARNING: NLLB model not found
    echo Run 'python setup_models.py' to download and convert models
    echo.
    echo Starting anyway (NLLB translation will not be available)
    timeout /t 3
)

REM Start the server
echo Starting BabbleFish server...
echo.
echo API will be available at: http://localhost:8000
echo API docs: http://localhost:8000/docs
echo.
python main.py

pause
