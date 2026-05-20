@echo off
REM =====================================================
REM Unified Launcher - HR + Factory Systems (Merged Mode)
REM =====================================================
cd /d %~dp0

:: Try to activate venv
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Start Unified System (HR + Manufacturing)
echo [1/1] Starting Merged System on Port 5000...
:: Using system python if venv activation is successful
start "Unified System" python run.py

REM Wait for system to initialize
echo Waiting for server to initialize...
set "UNIFIED_URL=http://127.0.0.1:5000/manufacturing"
timeout /t 5

echo [OK] Opening Manufacturing Dashboard...
start "" "%UNIFIED_URL%"

echo.
echo =====================================================
echo [DONE] The system is now running on Port 5000.
echo Access Manufacturing at: %UNIFIED_URL%
echo Access HR System at: http://127.0.0.1:5000
echo =====================================================
echo.

pause
