@echo off
setlocal
cd /d "%~dp0"

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "OFFLINE_DIR=%SCRIPT_DIR%\offline_packages"
set "REQ_FILE=%OFFLINE_DIR%\requirements.txt"

echo ================================================
echo HR System Offline Installer
echo ================================================
echo.

if not exist "%OFFLINE_DIR%" (
    echo [ERROR] offline_packages folder was not found.
    pause
    exit /b 1
)

if not exist "%REQ_FILE%" (
    echo [ERROR] requirements.txt was not found inside offline_packages.
    pause
    exit /b 1
)

call :resolve_python
if errorlevel 1 (
    echo [ERROR] Python 3.11+ was not found on this machine.
    pause
    exit /b 1
)

echo [INFO] Using %PYTHON_CMD%
%PYTHON_CMD% -m ensurepip --default-pip >nul 2>&1
echo [INFO] Installing packages from "%OFFLINE_DIR%"...
%PYTHON_CMD% -m pip install --no-index --find-links="%OFFLINE_DIR%" -r "%REQ_FILE%"
if errorlevel 1 (
    echo [ERROR] Offline installation failed.
    pause
    exit /b 1
)

echo.
echo [OK] Offline installation completed successfully.
pause
exit /b 0

:resolve_python
where py >nul 2>&1
if not errorlevel 1 (
    py -3.11 --version >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_CMD=py -3.11"
        exit /b 0
    )
    py --version >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_CMD=py"
        exit /b 0
    )
)

where python >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    exit /b 0
)

exit /b 1
