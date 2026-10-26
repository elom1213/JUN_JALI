@echo off
rem ============================================================================
rem  JUN_JALI - Explorer shortcuts with the tool icons  (double-click, or run by setup_*.bat)
rem  A .bat file cannot carry its own icon, so this makes a .lnk next to it:
rem    "STT Converter.lnk"       -> Run_STT_Converter.bat       (tools\STT_Converter\icon\*.ico)
rem    "VisemeNet Converter.lnk" -> Run_VisemeNet_Converter.bat (tools\VisemeNet_Converter\icon\*.ico)
rem  A .lnk stores absolute paths - run this again after moving the folder. (*.lnk is not in git)
rem ============================================================================
setlocal
chcp 65001 >nul
cd /d "%~dp0"
call :make "STT Converter" "Run_STT_Converter.bat" "tools\STT_Converter\icon\STT_Converter.ico"
call :make "VisemeNet Converter" "Run_VisemeNet_Converter.bat" "tools\VisemeNet_Converter\icon\VisemeNet_Converter.ico"
exit /b 0

:make
if not exist "%~dp0%~2" exit /b 0
if not exist "%~dp0%~3" exit /b 0
rem paths go through environment variables (spaces or quotes in the path cannot break the PowerShell command)
set "JALI_LNK=%~dp0%~1.lnk"
set "JALI_TARGET=%~dp0%~2"
set "JALI_ICON=%~dp0%~3"
set "JALI_DIR=%~dp0"
rem WindowStyle 7 = minimized: the bat's console only flashes in the taskbar before pythonw opens the window
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:JALI_LNK);" ^
  "$s.TargetPath=$env:JALI_TARGET; $s.WorkingDirectory=$env:JALI_DIR.TrimEnd('\');" ^
  "$s.IconLocation=$env:JALI_ICON + ',0'; $s.WindowStyle=7; $s.Save()" >nul 2>&1
if errorlevel 1 (
    echo [WARN] Could not make "%~1.lnk" - use %~2 directly.
    exit /b 0
)
echo       shortcut: %~1.lnk
exit /b 0
