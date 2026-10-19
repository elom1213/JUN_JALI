@echo off
rem ============================================================================
rem  JUN_JALI - VisemeNet Converter  (double-click to open the window)
rem  Needs the environment from setup_env.bat. Startup errors are shown in a
rem  message box and saved to tools\VisemeNet_Converter\data\startup_error.log
rem ============================================================================
setlocal
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    echo [ERROR] Environment not found. Double-click setup_env.bat first.
    pause
    exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" "tools\VisemeNet_Converter\launch.py"
exit /b 0
