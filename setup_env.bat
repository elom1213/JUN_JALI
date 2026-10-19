@echo off
rem ============================================================================
rem  JUN_JALI - VisemeNet inference environment setup  (double-click to run)
rem  Python Script by Ji Hun Park / last Update date : 2026-10-19
rem
rem  1) find 64-bit Python 3.9 - 3.11 (py launcher first, then PATH; the Microsoft
rem     Store "python" shortcut is skipped). Offers a winget install when missing.
rem  2) create / reuse .venv   3) pip install -r requirements.txt
rem  4) self test: load the model and convert test_audio\coffee_xxxx.wav
rem  Re-running is safe. Options: --force (rebuild .venv), --nopause (for scripts)
rem  Full output: setup_env.log
rem ============================================================================
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

set "LOG=%~dp0setup_env.log"
set "VPY=%~dp0.venv\Scripts\python.exe"
set "FORCE=0"
set "NOPAUSE=0"
for %%A in (%*) do (
    if /i "%%~A"=="--force" set "FORCE=1"
    if /i "%%~A"=="--nopause" set "NOPAUSE=1"
)

> "%LOG%" echo JUN_JALI setup - %DATE% %TIME%
call :say "============================================================"
call :say " JUN_JALI - VisemeNet environment setup"
call :say " Folder: %CD%"
call :say "============================================================"

if not exist "visemenet_frozen.pb" (
    call :say "[ERROR] visemenet_frozen.pb not found - run this file from the JUN_JALI folder."
    goto :end_fail
)
if not exist "vendor\Framework\qt\qt.py" (
    call :say "[ERROR] vendor\Framework is missing - the repository is incomplete."
    goto :end_fail
)

rem ---------------------------------------------------------------- 1) Python
call :say ""
call :say "[1/4] Looking for 64-bit Python 3.9 - 3.11 ..."
set "PY="
call :find_python
if defined PY goto :have_python

call :say "[WARN] Python 3.9 - 3.11 (64-bit) was not found."
where winget >nul 2>&1
if errorlevel 1 goto :no_python
choice /c YN /m "Install Python 3.11 for this user now with winget"
if errorlevel 2 goto :no_python
call :say "       Installing Python 3.11 with winget ..."
winget install -e --id Python.Python.3.11 --scope user --accept-package-agreements --accept-source-agreements >> "%LOG%" 2>&1
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "PY="%LOCALAPPDATA%\Programs\Python\Python311\python.exe""
if not defined PY call :find_python
if defined PY goto :have_python

:no_python
call :say "[ERROR] Python 3.9 - 3.11 (64-bit) is required."
call :say "        Download Python 3.11: https://www.python.org/downloads/release/python-3119/"
call :say "        In the installer, check 'Add python.exe to PATH', then run this file again."
goto :end_fail

:have_python
for /f "delims=" %%V in ('%PY% -c "import sys; print(sys.version.split()[0])"') do set "PYVER=%%V"
call :say "      found: %PY%  (Python %PYVER%)"

rem ---------------------------------------------------------------- 2) .venv
call :say ""
call :say "[2/4] Preparing .venv ..."
if "%FORCE%"=="1" if exist ".venv" (
    call :say "      --force: removing the old .venv"
    rmdir /s /q ".venv"
)
if exist "%VPY%" (
    "%VPY%" -c "import sys; sys.exit(0 if (3,9) <= sys.version_info[:2] <= (3,11) else 1)" >nul 2>&1
    if errorlevel 1 (
        call :say "      existing .venv uses an unsupported Python - rebuilding"
        rmdir /s /q ".venv"
    ) else (
        call :say "      reusing the existing .venv"
    )
)
if not exist "%VPY%" (
    %PY% -m venv .venv >> "%LOG%" 2>&1
    if errorlevel 1 (
        call :say "[ERROR] Could not create .venv - see setup_env.log"
        goto :end_fail
    )
    call :say "      created .venv"
)

rem ---------------------------------------------------------------- 3) packages
call :say ""
call :say "[3/4] Installing packages (first time: several minutes, about 1.6 GB) ..."
"%VPY%" -m pip install --upgrade pip >> "%LOG%" 2>&1
"%VPY%" -m pip install -r requirements.txt >> "%LOG%" 2>&1
if errorlevel 1 goto :pip_fail
call :say "      packages OK"

rem ---------------------------------------------------------------- 4) self test
call :say ""
call :say "[4/4] Self test (loads the model and converts test_audio\coffee_xxxx.wav) ..."
set "ST=%TEMP%\jun_jali_selftest.txt"
"%VPY%" "tools\selftest.py" > "%ST%" 2>> "%LOG%"
set "STRC=%ERRORLEVEL%"
type "%ST%"
type "%ST%" >> "%LOG%"
if not "%STRC%"=="0" (
    call :say "[ERROR] Self test failed - see the message above and setup_env.log"
    goto :end_fail
)

call :say ""
call :say "============================================================"
call :say " SETUP OK"
call :say " Next: double-click Run_VisemeNet_Converter.bat"
call :say "============================================================"
if "%NOPAUSE%"=="0" pause
exit /b 0

rem ============================================================================
:pip_fail
call :say "[ERROR] Package installation failed. Last lines of setup_env.log:"
powershell -NoProfile -Command "Get-Content -Tail 15 -LiteralPath '%LOG%'"
findstr /i /c:"No matching distribution" "%LOG%" >nul && call :say "  - Hint: this Python version is not supported by tensorflow-cpu 2.15 (use 3.9 - 3.11, 64-bit)."
findstr /i /c:"No such file or directory" /c:"path too long" "%LOG%" >nul && call :say "  - Hint: Windows 260-character path limit. Move JUN_JALI to a shorter path (e.g. C:\JUN_JALI)."
findstr /i /c:"SSL" /c:"timed out" /c:"ProxyError" "%LOG%" >nul && call :say "  - Hint: network / proxy problem. Check the internet connection or set a pip proxy."
goto :end_fail

:end_fail
call :say ""
call :say "SETUP FAILED - full log: %LOG%"
if "%NOPAUSE%"=="0" pause
exit /b 1

rem ---------------------------------------------------------------------------
:find_python
rem py launcher (3.11 -> 3.10 -> 3.9), 64-bit only
for %%V in (3.11 3.10 3.9) do (
    if not defined PY (
        py -%%V -c "import sys; sys.exit(0 if sys.maxsize > 2**32 else 1)" >nul 2>&1
        if not errorlevel 1 set "PY=py -%%V"
    )
)
if defined PY exit /b 0
rem python on PATH - skip the Microsoft Store shortcut (WindowsApps)
for /f "delims=" %%P in ('where python 2^>nul') do (
    if not defined PY call :try_python "%%P"
)
exit /b 0

:try_python
echo %~1 | find /i "WindowsApps" >nul
if not errorlevel 1 exit /b 0
"%~1" -c "import sys; sys.exit(0 if (3,9) <= sys.version_info[:2] <= (3,11) and sys.maxsize > 2**32 else 1)" >nul 2>&1
if not errorlevel 1 set "PY="%~1""
exit /b 0

:say
echo(%~1
>> "%LOG%" echo(%~1
exit /b 0
