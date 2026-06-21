@echo off
netstat -an | find ":5001" >nul 2>&1
if %errorlevel% equ 0 (
    echo Server already running...
) else (
    start "Brainrot Math" /min python "C:\Projects\Brainrot Math\app.py"
    timeout /t 2 /nobreak >nul
)
start "" "http://localhost:5001"
