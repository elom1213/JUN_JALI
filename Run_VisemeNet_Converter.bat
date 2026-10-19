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
rem the .venv points at the Python it was made from (absolute path) - moving the folder or deleting
rem .python\ breaks it, and pythonw would fail without a console. Check first.
".venv\Scripts\python.exe" -c "import PySide6" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] The environment does not run - the folder was moved or the Python it used is gone.
    echo         Double-click setup_env.bat again ^(add --force if it keeps failing^).
    pause
    exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" "tools\VisemeNet_Converter\launch.py"
exit /b 0
