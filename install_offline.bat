@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "OFFLINE_DIR=%SCRIPT_DIR%\offline_packages"
set "REQ_FILE=%OFFLINE_DIR%\requirements.txt"
set "VENV_DIR=%SCRIPT_DIR%\.venv"
set "LOG_FILE=%SCRIPT_DIR%\offline_install.log"

echo ================================================
echo HR System Offline Installer
echo ================================================
echo.
echo Log file: %LOG_FILE%
echo Started at %DATE% %TIME% > "%LOG_FILE%"

if not exist "%OFFLINE_DIR%" (
    echo [ERROR] offline_packages folder was not found.
    echo [ERROR] offline_packages folder was not found. >> "%LOG_FILE%"
    pause
    exit /b 1
)

if not exist "%REQ_FILE%" (
    echo [ERROR] requirements.txt was not found inside offline_packages.
    echo [ERROR] requirements.txt was not found inside offline_packages. >> "%LOG_FILE%"
    pause
    exit /b 1
)

call :ensure_windows_x64
if errorlevel 1 goto failed

call :resolve_python311
if errorlevel 1 (
    call :install_python311
    if errorlevel 1 goto failed
    call :resolve_python311
    if errorlevel 1 (
        echo [ERROR] Python 3.11 could not be found after installation.
        echo [ERROR] Python 3.11 could not be found after installation. >> "%LOG_FILE%"
        goto failed
    )
)

echo [INFO] Using "%PYTHON_EXE%" %PYTHON_ARGS%
echo [INFO] Using "%PYTHON_EXE%" %PYTHON_ARGS% >> "%LOG_FILE%"

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [INFO] Creating virtual environment .venv...
    echo [INFO] Creating virtual environment .venv... >> "%LOG_FILE%"
    "%PYTHON_EXE%" %PYTHON_ARGS% -m venv "%VENV_DIR%" >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        goto failed
    )
)

set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
if not exist "%VENV_PY%" (
    echo [ERROR] Virtual environment Python was not found: %VENV_PY%
    echo [ERROR] Virtual environment Python was not found: %VENV_PY% >> "%LOG_FILE%"
    goto failed
)

echo [INFO] Preparing pip...
"%VENV_PY%" -m ensurepip --upgrade >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to prepare pip.
    goto failed
)

echo [INFO] Installing packages from "%OFFLINE_DIR%"...
echo [INFO] Installing packages from "%OFFLINE_DIR%"... >> "%LOG_FILE%"
"%VENV_PY%" -m pip install --no-index --only-binary=:all: --find-links="%OFFLINE_DIR%" --upgrade -r "%REQ_FILE%" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [ERROR] Offline package installation failed.
    echo [INFO] See "%LOG_FILE%" for details.
    goto failed
)

echo [INFO] Verifying installed packages...
"%VENV_PY%" -c "import flask, flask_wtf, sqlalchemy, pandas, openpyxl, PIL, qrcode, dotenv, git; print('OK')" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [ERROR] Package verification failed.
    echo [INFO] See "%LOG_FILE%" for details.
    goto failed
)

echo [INFO] Checking package compatibility...
"%VENV_PY%" -m pip check >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [ERROR] Package compatibility check failed.
    echo [INFO] See "%LOG_FILE%" for details.
    goto failed
)

echo [INFO] Verifying application startup imports...
"%VENV_PY%" -c "from app import create_app; create_app(); print('APP_OK')" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [ERROR] Application import verification failed.
    echo [INFO] See "%LOG_FILE%" for details.
    goto failed
)

echo.
echo [OK] Offline installation completed successfully.
echo [OK] Run start_hr.bat to start the system.
echo [OK] Offline installation completed successfully. >> "%LOG_FILE%"
pause
exit /b 0

:ensure_windows_x64
if /I "%PROCESSOR_ARCHITECTURE%"=="AMD64" exit /b 0
if /I "%PROCESSOR_ARCHITEW6432%"=="AMD64" exit /b 0
if exist "%SystemRoot%\SysWOW64" exit /b 0
echo [ERROR] This offline package is for 64-bit Windows only.
echo [ERROR] This offline package is for 64-bit Windows only. >> "%LOG_FILE%"
exit /b 1

:resolve_python311
if exist "%VENV_DIR%\Scripts\python.exe" (
    "%VENV_DIR%\Scripts\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 11) else 1)" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
        set "PYTHON_ARGS="
        exit /b 0
    )
)

where py >nul 2>&1
if not errorlevel 1 (
    py -3.11 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 11) else 1)" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=py"
        set "PYTHON_ARGS=-3.11"
        exit /b 0
    )
)

for %%P in (
    "%LocalAppData%\Programs\Python\Python311\python.exe"
    "%ProgramFiles%\Python311\python.exe"
    "%ProgramFiles(x86)%\Python311\python.exe"
) do (
    if exist "%%~P" (
        "%%~P" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 11) else 1)" >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_EXE=%%~P"
            set "PYTHON_ARGS="
            exit /b 0
        )
    )
)

where python >nul 2>&1
if not errorlevel 1 (
    python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 11) else 1)" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=python"
        set "PYTHON_ARGS="
        exit /b 0
    )
)

exit /b 1

:install_python311
set "PY_INSTALLER="
for %%F in ("%OFFLINE_DIR%\python-3.11.*-amd64.exe") do (
    if exist "%%~F" set "PY_INSTALLER=%%~F"
)

if "%PY_INSTALLER%"=="" (
    echo [ERROR] Python 3.11 installer was not found in offline_packages.
    echo [ERROR] Add python-3.11.9-amd64.exe to offline_packages, then run this file again.
    echo [ERROR] Python 3.11 installer was not found in offline_packages. >> "%LOG_FILE%"
    exit /b 1
)

echo [INFO] Installing Python from "%PY_INSTALLER%"...
echo [INFO] Installing Python from "%PY_INSTALLER%"... >> "%LOG_FILE%"
"%PY_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 Include_pip=1 Include_test=0 Shortcuts=0 >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo [ERROR] Python installer failed.
    exit /b 1
)
exit /b 0

:failed
echo.
echo [FAILED] Offline installation did not complete.
echo [INFO] Open "%LOG_FILE%" to see the exact error.
pause
exit /b 1
