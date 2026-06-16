@echo off
REM =====================================================
REM Unified Launcher - HR + Factory Systems (Merged Mode)
REM =====================================================
setlocal EnableDelayedExpansion

cd /d "%~dp0"

REM =====================================================
REM [1] Verify run.py exists before proceeding
REM =====================================================
if not exist "%~dp0run.py" (
    echo [ERROR] run.py not found in: %~dp0
    echo [ERROR] Aborting launch for security reasons.
    pause
    exit /b 1
)

REM =====================================================
REM [2] Activate virtual environment (mandatory)
REM =====================================================
if exist "%~dp0.venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call "%~dp0.venv\Scripts\activate.bat"
    if errorlevel 1 (
        echo [ERROR] Failed to activate virtual environment.
        echo [ERROR] Aborting to avoid running with unverified system Python.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment activated.
) else (
    echo [ERROR] Virtual environment not found at .venv\Scripts\activate.bat
    echo [ERROR] Aborting launch. Please set up the virtual environment first.
    pause
    exit /b 1
)

REM =====================================================
REM [3] Start Unified System (HR + Manufacturing)
REM =====================================================
echo [1/1] Starting Merged System on Port 5000...
start "Unified System" python "%~dp0run.py"

REM =====================================================
REM [4] Wait for server to initialize
REM =====================================================
echo Waiting for server to initialize...
timeout /t 5 /nobreak > nul

REM =====================================================
REM [5] Open dashboards using hardcoded safe URLs
REM =====================================================
echo [OK] Opening Manufacturing Dashboard...
start "" "http://127.0.0.1:5000/manufacturing"

echo.
echo =====================================================
echo [DONE] The system is now running on Port 5000.
echo Access Manufacturing at: http://127.0.0.1:5000/manufacturing
echo Access HR System at:     http://127.0.0.1:5000
echo =====================================================
echo.

endlocal
pause
