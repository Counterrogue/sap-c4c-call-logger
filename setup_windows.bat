@echo off
setlocal
cd /d "%~dp0"
echo Creating Python environment...
py -3 -m venv .venv
if errorlevel 1 (
    echo Python launcher not found. Install Python 3.11 or 3.12.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m playwright install chromium
if errorlevel 1 goto failed
echo Setup complete.
pause
exit /b 0
:failed
echo Setup failed.
pause
exit /b 1
