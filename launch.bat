@echo off
netstat -an | find ":5001" >nul 2>&1
if %errorlevel% equ 0 (
    echo Server already running...
) else (
    start "Arkadian's Game Hub" /min python "C:\Projects\Arkadian's Game Hub\app.py"
    timeout /t 2 /nobreak >nul
)
start "" "http://localhost:5001"
