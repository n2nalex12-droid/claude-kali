@echo off
REM Universal Windows Launcher for Local Claude Code
set DIR=%~dp0
cd /d "%DIR%"

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [!] python not found in PATH. Please install Python 3.10+ from python.org
    pause
    exit /b 1
)

python agent.py %*
pause
