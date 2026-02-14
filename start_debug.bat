@echo off
REM Debug starter that runs Flask app in the current console so we can see errors
cd /d %~dp0

echo [INFO] Using Python executable:
py --version
echo [INFO] Running Flask (foreground)
py -3 run.py

echo [INFO] The server has stopped; press a key to continue...
pause
