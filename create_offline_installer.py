import shutil
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
OFFLINE_DIR = BASE_DIR / "offline_packages"
REQUIREMENTS_FILE = BASE_DIR / "requirements.txt"
OFFLINE_REQUIREMENTS_FILE = OFFLINE_DIR / "requirements.txt"
INSTALL_SCRIPT_PATH = BASE_DIR / "install_offline.bat"


def run_command(command):
    subprocess.check_call(command, cwd=str(BASE_DIR))


def copy_requirements_file():
    OFFLINE_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REQUIREMENTS_FILE, OFFLINE_REQUIREMENTS_FILE)
    print(f"Copied requirements file to: {OFFLINE_REQUIREMENTS_FILE}")


def download_requirements():
    print(f"Downloading packages from {REQUIREMENTS_FILE.name} to {OFFLINE_DIR.name}...")
    run_command(
        [
            sys.executable,
            "-m",
            "pip",
            "download",
            "-r",
            str(REQUIREMENTS_FILE),
            "-d",
            str(OFFLINE_DIR),
        ]
    )


def ensure_cached_wheels(packages):
    if not packages:
        return

    print("Checking cached wheels for additional dependencies...")
    run_command(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--wheel-dir",
            str(OFFLINE_DIR),
            *packages,
        ]
    )


def build_install_script():
    script_lines = [
        "@echo off",
        "setlocal",
        'cd /d "%~dp0"',
        "",
        'set "SCRIPT_DIR=%~dp0"',
        'if "%SCRIPT_DIR:~-1%"=="\\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"',
        'set "OFFLINE_DIR=%SCRIPT_DIR%\\offline_packages"',
        'set "REQ_FILE=%OFFLINE_DIR%\\requirements.txt"',
        "",
        "echo ================================================",
        "echo HR System Offline Installer",
        "echo ================================================",
        "echo.",
        'if not exist "%OFFLINE_DIR%" (',
        '    echo [ERROR] offline_packages folder was not found.',
        "    pause",
        "    exit /b 1",
        ")",
        'if not exist "%REQ_FILE%" (',
        '    echo [ERROR] requirements.txt was not found inside offline_packages.',
        "    pause",
        "    exit /b 1",
        ")",
        "",
        "call :resolve_python",
        "if errorlevel 1 (",
        '    echo [ERROR] Python 3.11+ was not found on this machine.',
        "    pause",
        "    exit /b 1",
        ")",
        "",
        'echo [INFO] Using %PYTHON_CMD%',
        '%PYTHON_CMD% -m ensurepip --default-pip >nul 2>&1',
        'echo [INFO] Installing packages from "%OFFLINE_DIR%"...',
        '%PYTHON_CMD% -m pip install --no-index --find-links="%OFFLINE_DIR%" -r "%REQ_FILE%"',
        "if errorlevel 1 (",
        '    echo [ERROR] Offline installation failed.',
        "    pause",
        "    exit /b 1",
        ")",
        "",
        "echo.",
        "echo [OK] Offline installation completed successfully.",
        "pause",
        "exit /b 0",
        "",
        ":resolve_python",
        "where py >nul 2>&1",
        "if not errorlevel 1 (",
        "    py -3.11 --version >nul 2>&1",
        "    if not errorlevel 1 (",
        '        set "PYTHON_CMD=py -3.11"',
        "        exit /b 0",
        "    )",
        "    py --version >nul 2>&1",
        "    if not errorlevel 1 (",
        '        set "PYTHON_CMD=py"',
        "        exit /b 0",
        "    )",
        ")",
        "",
        "where python >nul 2>&1",
        "if not errorlevel 1 (",
        '    set "PYTHON_CMD=python"',
        "    exit /b 0",
        ")",
        "",
        "exit /b 1",
    ]
    INSTALL_SCRIPT_PATH.write_text("\n".join(script_lines) + "\n", encoding="utf-8")
    print(f"Created installation script: {INSTALL_SCRIPT_PATH}")


def create_offline_installer():
    print("Creating offline installer...")

    if not REQUIREMENTS_FILE.exists():
        print(f"Error: requirements file not found: {REQUIREMENTS_FILE}")
        return

    copy_requirements_file()

    try:
        download_requirements()
        ensure_cached_wheels(
            [
                "GitPython==3.1.46",
                "gitdb==4.0.12",
                "smmap==5.0.2",
            ]
        )
    except subprocess.CalledProcessError as error:
        print(f"Error preparing offline packages: {error}")
        return

    build_install_script()

    print("\nOffline installer created successfully!")
    print(f"Copy '{OFFLINE_DIR.name}' and '{INSTALL_SCRIPT_PATH.name}' to the target machine.")
    print("Then run 'install_offline.bat' on the target machine.")


if __name__ == "__main__":
    create_offline_installer()
