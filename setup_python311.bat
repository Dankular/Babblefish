@echo off
REM Setup Python 3.11 environment for XTTS-v2

echo ========================================
echo Setting up Python 3.11 for XTTS-v2
echo ========================================

REM Check if conda is available
where conda >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Conda not found. Please install Miniconda or Anaconda first.
    echo Download from: https://docs.conda.io/en/latest/miniconda.html
    pause
    exit /b 1
)

echo [1/4] Creating Python 3.11 environment...
conda create -n babblefish-tts python=3.11 -y
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to create conda environment
    pause
    exit /b 1
)

echo.
echo [2/4] Activating environment...
call conda activate babblefish-tts
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to activate environment
    pause
    exit /b 1
)

echo.
echo [3/4] Installing dependencies...
pip install -r server\requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [4/4] Verifying installation...
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA Available: {torch.cuda.is_available()}')"
python -c "from TTS.api import TTS; print('TTS (XTTS-v2): OK')"
python -c "from faster_whisper import WhisperModel; print('faster-whisper: OK')"
python -c "import transformers; print('transformers: OK')"

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To use this environment:
echo   conda activate babblefish-tts
echo.
echo To test the pipeline:
echo   python test_pipeline.py
echo.
echo To start the server:
echo   cd server
echo   python tts_server.py
echo.
pause
