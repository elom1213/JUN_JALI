@echo off
rem ============================================================================
rem  JUN_JALI - VisemeNet inference environment setup  (double-click to run)
rem  Python Script by Ji Hun Park / last Update date : 2026-10-20
rem
rem  TensorFlow 2.15 (the model runtime) needs 64-bit Python 3.9 - 3.11.
rem  1) find one: py launcher (3.11 / 3.10 / 3.9), python on PATH, or the private
rem     copy in .python\ . Each candidate is checked by RUNNING it and reading the
rem     version it prints - the new Python install manager's "py -3.11" prints an
rem     error but still exits 0 when 3.11 is not installed (Windows 10, Python 3.14).
rem  2) none found (e.g. only Python 3.14): offer to download a PRIVATE Python 3.11.9
rem     into .python\ (python.org NuGet package, ~17 MB, SHA-256 checked). Nothing is
rem     installed on the system and the existing Python is not touched.
rem  3) create / reuse .venv   4) pip install -r requirements.txt   5) self test
rem  Re-running is safe. Options: --force (rebuild .venv), --yes (download without
rem  asking), --nopause (for scripts). Full output: setup_env.log
rem ============================================================================
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
rem Isolate from the PC's own Python / conda (e.g. Python 3.14 with PYTHONPATH set, another conda
rem activated): their variables would leak into this tool's Python and break imports.
set "PYTHONHOME="
set "PYTHONPATH="
set "PYTHONSTARTUP="
set "PYTHONNOUSERSITE=1"

set "LOG=%~dp0setup_env.log"
set "VPY=%~dp0.venv\Scripts\python.exe"
set "PRIV=%~dp0.python"
set "PRIV_PY=%~dp0.python\python.exe"
set "PY_URL=https://www.nuget.org/api/v2/package/python/3.11.9"
set "PY_SHA=9283876d58c017e0e846f95b490da3bca0fc0a6ee1134b2870677cfb7eec3c67"
set "PROBE=%TEMP%\jun_jali_probe.txt"
set "FORCE=0"
set "NOPAUSE=0"
set "YES=0"
for %%A in (%*) do (
    if /i "%%~A"=="--force" set "FORCE=1"
    if /i "%%~A"=="--nopause" set "NOPAUSE=1"
    if /i "%%~A"=="--yes" set "YES=1"
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
call :say "[1/5] Looking for 64-bit Python 3.9 - 3.11 (TensorFlow 2.15 does not run on newer Python) ..."
set "PY="
set "PYVER="
set "OTHERS="
call :find_python
if defined PY goto :have_python

call :say "[WARN] No 64-bit Python 3.9 - 3.11 found.%OTHERS%"
call :say "       This tool can download its own Python 3.11.9 into this folder (.python\, about 17 MB)."
call :say "       Nothing is installed on the system and your other Python versions are not changed."
if "%YES%"=="1" goto :get_private
choice /c YN /m "Download the private Python 3.11 now"
if errorlevel 2 goto :no_python

:get_private
call :download_python
if errorlevel 1 goto :end_fail
call :probe "%PRIV_PY%"
if defined P_OK (
    set "PY="%PRIV_PY%""
    set "PYVER=%P_VER%"
    goto :have_python
)
call :say "[ERROR] The downloaded Python does not run - see setup_env.log"
goto :end_fail

:no_python
call :say "[ERROR] Python 3.9 - 3.11 (64-bit) is required."
call :say "        Run this file again and answer Y to download a private copy, or install Python 3.11:"
call :say "        https://www.python.org/downloads/release/python-3119/"
goto :end_fail

:have_python
call :say "      found: %PY%  (Python %PYVER%)"

rem ---------------------------------------------------------------- 2) .venv
call :say ""
call :say "[2/5] Preparing .venv ..."
if "%FORCE%"=="1" if exist ".venv" (
    call :say "      --force: removing the old .venv"
    rmdir /s /q ".venv"
)
if exist "%VPY%" (
    call :probe "%VPY%"
    if not defined P_OK (
        call :say "      existing .venv does not run or uses an unsupported Python - rebuilding"
        rmdir /s /q ".venv"
    ) else (
        call :say "      reusing the existing .venv"
    )
) else if exist ".venv" (
    call :say "      removing a broken .venv (no python.exe)"
    rmdir /s /q ".venv"
)
if not exist "%VPY%" (
    call %PY% -m venv .venv >> "%LOG%" 2>&1
    if not exist "%VPY%" (
        call :say "[ERROR] Could not create .venv - see setup_env.log"
        goto :end_fail
    )
    call :say "      created .venv"
)

rem ---------------------------------------------------------------- 3) packages
call :say ""
call :say "[3/5] Installing packages (first time: several minutes, about 1.6 GB) ..."
"%VPY%" -m pip install --upgrade pip >> "%LOG%" 2>&1
"%VPY%" -m pip install -r requirements.txt >> "%LOG%" 2>&1
if errorlevel 1 goto :pip_fail
call :say "      packages OK"

rem ---------------------------------------------------------------- 4) self test
call :say ""
call :say "[4/5] Self test (loads the model and converts test_audio\coffee_xxxx.wav) ..."
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
call :say "[5/5] Done."
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
rem py launcher (3.11 -> 3.10 -> 3.9). Exit codes are not trusted - see the header.
for %%V in (3.11 3.10 3.9) do (
    if not defined PY call :try_cmd "py -%%V"
)
if defined PY exit /b 0
rem python on PATH - skip the Microsoft Store shortcut (WindowsApps)
for /f "delims=" %%P in ('where python 2^>nul') do (
    if not defined PY call :try_path "%%P"
)
if defined PY exit /b 0
rem the private copy downloaded by an earlier run
if exist "%PRIV_PY%" call :try_path "%PRIV_PY%"
if defined PY exit /b 0
rem nothing usable - note what IS installed for the message (e.g. Python 3.14)
call :probe "py"
if defined P_VER call :note_other "%P_VER%"
exit /b 0

:try_cmd
call :probe "%~1"
if defined P_OK (
    set "PY=%~1"
    set "PYVER=%P_VER%"
) else if defined P_VER (
    call :note_other "%P_VER%"
)
exit /b 0

:try_path
echo %~1 | find /i "WindowsApps" >nul
if not errorlevel 1 exit /b 0
call :probe "%~1"
if defined P_OK (
    set "PY="%~1""
    set "PYVER=%P_VER%"
) else if defined P_VER (
    call :note_other "%P_VER%"
)
exit /b 0

:note_other
echo "%OTHERS%" | find "%~1" >nul
if errorlevel 1 set "OTHERS=%OTHERS% Found Python %~1 (not supported)."
exit /b 0

:probe
rem Runs the interpreter and reads what it prints. Sets P_VER (e.g. 3.14) and P_OK (3.9 - 3.11, 64-bit).
rem  %~1 = "py -3.11" (command) or a full path to python.exe
set "P_OK="
set "P_VER="
set "P_LINE="
if exist "%~1" (
    "%~1" -c "import sys; print('JUNPY', *sys.version_info[:2], 64 if sys.maxsize > 2**32 else 32)" > "%PROBE%" 2>nul
) else (
    call %~1 -c "import sys; print('JUNPY', *sys.version_info[:2], 64 if sys.maxsize > 2**32 else 32)" > "%PROBE%" 2>nul
)
if exist "%PROBE%" set /p P_LINE=<"%PROBE%"
del "%PROBE%" >nul 2>&1
if not defined P_LINE exit /b 0
for /f "tokens=1-4" %%a in ("%P_LINE%") do (
    if "%%a"=="JUNPY" (
        set "P_VER=%%b.%%c"
        if "%%b"=="3" if "%%d"=="64" (
            if "%%c"=="9" set "P_OK=1"
            if "%%c"=="10" set "P_OK=1"
            if "%%c"=="11" set "P_OK=1"
        )
    )
)
exit /b 0

:download_python
rem python.org NuGet package (a full Python 3.11.9 without an installer) -> .python\
call :say "      downloading Python 3.11.9 (python.org NuGet package) ..."
if exist "%PRIV%" rmdir /s /q "%PRIV%"
if exist "%~dp0.python_dl" rmdir /s /q "%~dp0.python_dl"
mkdir "%~dp0.python_dl"
rem path / url / hash go through environment variables (spaces or quotes in the path cannot break the PowerShell command)
set "JALI_DL=%~dp0.python_dl"
set "JALI_DST=%PRIV%"
set "JALI_URL=%PY_URL%"
set "JALI_SHA=%PY_SHA%"
rem Extract tools\* -> .python\ but SKIP tools\Lib\site-packages\ (the bundled pip / setuptools): it has the
rem deepest paths of the package (260-character limit in long folders) and is not needed - venv installs
rem pip from Lib\ensurepip.
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;" ^
  "$zip=Join-Path $env:JALI_DL 'python.zip'; $dst=$env:JALI_DST;" ^
  "(New-Object Net.WebClient).DownloadFile($env:JALI_URL, $zip);" ^
  "$s=[IO.File]::OpenRead($zip); $h=-join ([Security.Cryptography.SHA256]::Create().ComputeHash($s) | ForEach-Object { $_.ToString('x2') }); $s.Close();" ^
  "if ($h -ne $env:JALI_SHA) { throw ('SHA-256 mismatch: ' + $h) };" ^
  "Add-Type -AssemblyName System.IO.Compression.FileSystem;" ^
  "$za=[IO.Compression.ZipFile]::OpenRead($zip); $n=0;" ^
  "foreach ($e in $za.Entries) { $f=$e.FullName; if ($e.Name -and $f.StartsWith('tools/') -and -not $f.StartsWith('tools/Lib/site-packages/')) {" ^
  "  $out=Join-Path $dst ($f.Substring(6).Replace('/', '\')); [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($out)) | Out-Null;" ^
  "  [IO.Compression.ZipFileExtensions]::ExtractToFile($e, $out, $true); $n++ } };" ^
  "$za.Dispose(); Write-Output ('download + SHA-256 + extract OK: ' + $n + ' files')" >> "%LOG%" 2>&1
if errorlevel 1 (
    call :say "[ERROR] Download / extract failed - see setup_env.log"
    call :say "        Network or proxy problem, or the folder path is too long (move JUN_JALI to e.g. C:\JUN_JALI)."
    exit /b 1
)
rmdir /s /q "%~dp0.python_dl"
if not exist "%PRIV_PY%" (
    call :say "[ERROR] The downloaded package has no python.exe - see setup_env.log"
    exit /b 1
)
call :say "      private Python 3.11.9 is in .python\"
exit /b 0

:say
echo(%~1
>> "%LOG%" echo(%~1
exit /b 0
