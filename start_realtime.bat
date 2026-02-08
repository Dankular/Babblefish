@echo off
echo ========================================
echo  BabbleFish Real-time Translation
echo ========================================
echo.

REM Install additional dependencies
echo Installing real-time dependencies...
pip install -r requirements_realtime.txt --quiet
echo.

REM Start server
echo Starting real-time translation server...
echo.
echo Server will be available at:
echo   http://localhost:8001
echo.
echo Open this URL in your browser to use the real-time translator!
echo.
python realtime_server.py

pause
