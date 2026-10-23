@echo off
rem ============================================================================
rem  JUN_JALI - STT Converter  (double-click to open the window)
rem  Speech (wav) -> transcript (.lab) for the VisemeNet Converter Correct mode.
rem  Needs the environment from setup_stt.bat. Startup errors are shown in a
rem  message box and saved to tools\STT_Converter\data\startup_error.log
rem ============================================================================
setlocal
chcp 65001 >nul
cd /d "%~dp0"
rem Isolate from the PC's own Python / conda (e.g. Python 3.14 with PYTHONPATH set, another conda
rem activated): their variables would leak into this tool's Python and break imports.
set "PYTHONHOME="
set "PYTHONPATH="
set "PYTHONSTARTUP="
set "PYTHONNOUSERSITE=1"
set "PYTHONUTF8=1"
set "HF_HOME=%~dp0models"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"
if not exist ".venv_stt\Scripts\pythonw.exe" (
    echo [ERROR] Environment not found. Double-click setup_stt.bat first.
    pause
    exit /b 1
)
rem the .venv_stt points at the Python it was made from (absolute path) - moving the folder or deleting
rem .python\ breaks it, and pythonw would fail without a console. Check first.
".venv_stt\Scripts\python.exe" -c "import PySide6, faster_whisper" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] The environment does not run - the folder was moved or the Python it used is gone.
    echo         Double-click setup_stt.bat again ^(add --force if it keeps failing^).
    pause
    exit /b 1
)
start "" ".venv_stt\Scripts\pythonw.exe" "tools\STT_Converter\launch.py"
exit /b 0
