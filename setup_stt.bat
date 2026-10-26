@echo off
rem ============================================================================
rem  JUN_JALI - STT Converter environment setup  (double-click to run)
rem  Python Script by Ji Hun Park / last Update date : 2026-10-23
rem
rem  Speech (wav) -> transcript (.lab) with faster-whisper (large-v3-turbo), CPU or
rem  NVIDIA GPU (CUDA runtime comes from pip, no system CUDA needed).
rem  1) find 64-bit Python 3.9 - 3.11: the private copy in .python\ (shared with
rem     setup_env.bat), then py launcher / python on PATH. Each candidate is
rem     checked by RUNNING it (the new Python install manager's "py -3.11" prints
rem     an error but exits 0 when 3.11 is missing - Windows 10, Python 3.14).
rem  2) none found (e.g. only Python 3.14): download a PRIVATE Python 3.11.9 into
rem     .python\ (python.org NuGet package, ~17 MB, SHA-256 checked). Nothing is
rem     installed on the system and the existing Python is not touched.
rem  3) create / reuse .venv_stt   4) pip install -r requirements_stt.txt
rem  5) download the model into models\ (~1.6 GB)   6) self test (CPU)
rem  Re-running is safe. Options:
rem    --force               rebuild .venv_stt
rem    --yes                 download the private Python without asking
rem    --nopause             for scripts
rem    --no-system-python    never use the PC's Python: .python\ or download (D14)
rem    --use-system-python   also accept Python 3.12 - 3.14 from the PC (not tested)
rem    --offline             skip the model download (copy models\ from another PC)
rem    --model NAME          also download this model (large-v3, distil-large-v3.5,
rem                          kotoba-tech/kotoba-whisper-v2.0-faster, ...)
rem    --qwen                also install requirements_stt_qwen.txt (2nd engine)
rem  Full output: setup_stt.log
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
set "PYTHONUTF8=1"

set "LOG=%~dp0setup_stt.log"
set "VENV=%~dp0.venv_stt"
set "VPY=%~dp0.venv_stt\Scripts\python.exe"
set "PRIV=%~dp0.python"
set "PRIV_PY=%~dp0.python\python.exe"
set "MODELS=%~dp0models"
set "PY_URL=https://www.nuget.org/api/v2/package/python/3.11.9"
set "PY_SHA=9283876d58c017e0e846f95b490da3bca0fc0a6ee1134b2870677cfb7eec3c67"
set "PROBE=%TEMP%\jun_jali_stt_probe.txt"
set "DEFAULT_MODEL=large-v3-turbo"
set "FORCE=0"
set "NOPAUSE=0"
set "YES=0"
set "NOSYS=0"
set "USESYS=0"
set "OFFLINE=0"
set "QWEN=0"
set "MODEL2="
for %%A in (%*) do (
    if /i "%%~A"=="--force" set "FORCE=1"
    if /i "%%~A"=="--nopause" set "NOPAUSE=1"
    if /i "%%~A"=="--yes" set "YES=1"
    if /i "%%~A"=="--no-system-python" set "NOSYS=1"
    if /i "%%~A"=="--use-system-python" set "USESYS=1"
    if /i "%%~A"=="--offline" set "OFFLINE=1"
    if /i "%%~A"=="--qwen" set "QWEN=1"
)
rem "--model NAME": the token after --model (a plain loop cannot remember the previous token - walk the list)
call :parse_model %*

> "%LOG%" echo JUN_JALI STT setup - %DATE% %TIME%
call :say "============================================================"
call :say " JUN_JALI - STT Converter environment setup"
call :say " Folder: %CD%"
call :say "============================================================"
call :env_summary

if not exist "requirements_stt.txt" (
    call :say "[ERROR] requirements_stt.txt not found - run this file from the JUN_JALI folder."
    goto :end_fail
)
if not exist "vendor\Framework\qt\qt.py" (
    call :say "[ERROR] vendor\Framework is missing - the repository is incomplete."
    goto :end_fail
)
if not exist "tools\STT_Converter\selftest.py" (
    call :say "[ERROR] tools\STT_Converter is missing - the repository is incomplete."
    goto :end_fail
)

rem ---------------------------------------------------------------- 1) Python
call :say ""
if "%NOSYS%"=="1" (
    call :say "[1/6] --no-system-python: using the private Python in .python\ (download if missing) ..."
) else (
    call :say "[1/6] Looking for 64-bit Python 3.9 - 3.11 (.python\ first, then the PC) ..."
)
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
call :say "[ERROR] The downloaded Python does not run - see setup_stt.log"
goto :end_fail

:no_python
call :say "[ERROR] Python 3.9 - 3.11 (64-bit) is required."
call :say "        Run this file again and answer Y to download a private copy, or install Python 3.11:"
call :say "        https://www.python.org/downloads/release/python-3119/"
goto :end_fail

:have_python
call :say "      found: %PY%  (Python %PYVER%)"
>> "%LOG%" echo python used: %PY% (%PYVER%)

rem ---------------------------------------------------------------- 2) .venv_stt
call :say ""
call :say "[2/6] Preparing .venv_stt ..."
if "%FORCE%"=="1" if exist "%VENV%" (
    call :say "      --force: removing the old .venv_stt"
    rmdir /s /q "%VENV%"
)
if exist "%VPY%" (
    call :probe "%VPY%"
    if not defined P_OK (
        call :say "      existing .venv_stt does not run or uses an unsupported Python - rebuilding"
        rmdir /s /q "%VENV%"
    ) else (
        call :say "      reusing the existing .venv_stt"
    )
) else if exist "%VENV%" (
    call :say "      removing a broken .venv_stt (no python.exe)"
    rmdir /s /q "%VENV%"
)
if not exist "%VPY%" (
    call %PY% -m venv "%VENV%" >> "%LOG%" 2>&1
    if not exist "%VPY%" (
        call :say "[ERROR] Could not create .venv_stt - see setup_stt.log"
        goto :end_fail
    )
    call :say "      created .venv_stt"
)

rem ---------------------------------------------------------------- 3) packages
call :say ""
call :say "[3/6] Installing packages (first time: several minutes, about 1.5 GB with the CUDA runtime) ..."
"%VPY%" -m pip install --upgrade pip >> "%LOG%" 2>&1
"%VPY%" -m pip install -r requirements_stt.txt >> "%LOG%" 2>&1
if errorlevel 1 goto :pip_fail
if "%QWEN%"=="1" (
    if exist "requirements_stt_qwen.txt" (
        call :say "      --qwen: installing the Qwen3-ASR engine (PyTorch, several GB) ..."
        "%VPY%" -m pip install -r requirements_stt_qwen.txt >> "%LOG%" 2>&1
        if errorlevel 1 goto :pip_fail
    ) else (
        call :say "      --qwen: requirements_stt_qwen.txt is not in this repository yet - skipped"
    )
)
call :say "      packages OK"

rem ---------------------------------------------------------------- 4) model
call :say ""
if "%OFFLINE%"=="1" (
    call :say "[4/6] --offline: skipping the model download (models\ must be copied from another PC)"
    if not exist "%MODELS%\hub" call :say "[WARN] models\hub does not exist - the self test will fail (E41)"
) else (
    call :say "[4/6] Downloading the model %DEFAULT_MODEL% into models\ (about 1.6 GB, first time only) ..."
    call :get_model "%DEFAULT_MODEL%"
    if errorlevel 1 (
        call :say "[ERROR] Model download failed - check the internet connection, or copy models\ from another PC and run with --offline"
        goto :end_fail
    )
    if defined MODEL2 (
        call :say "      --model: downloading %MODEL2% ..."
        call :get_model "%MODEL2%"
        if errorlevel 1 (
            call :say "[ERROR] Model download failed for %MODEL2%"
            goto :end_fail
        )
    )
)

rem ---------------------------------------------------------------- 5) self test (CPU)
call :say ""
call :say "[5/6] Self test on CPU (loads the model and transcribes test_audio\coffee_xxxx.wav) ..."
set "ST=%TEMP%\jun_jali_stt_selftest.txt"
set "HF_HOME=%MODELS%"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"
"%VPY%" "tools\STT_Converter\selftest.py" > "%ST%" 2>> "%LOG%"
set "STRC=%ERRORLEVEL%"
type "%ST%"
type "%ST%" >> "%LOG%"
if not "%STRC%"=="0" (
    call :say "[ERROR] Self test failed - see the message above and setup_stt.log"
    goto :end_fail
)

call :say ""
call :say "[6/6] Done."
call "%~dp0make_shortcuts.bat"
call :say "============================================================"
call :say " SETUP OK"
call :say " Next: double-click the 'STT Converter' shortcut (or Run_STT_Converter.bat)"
call :say " GPU: pick 'Auto' or 'CUDA float16' in the Device box of the converter window."
call :say "============================================================"
if "%NOPAUSE%"=="0" pause
exit /b 0

rem ============================================================================
:pip_fail
call :say "[ERROR] Package installation failed. Last lines of setup_stt.log:"
powershell -NoProfile -Command "Get-Content -Tail 15 -LiteralPath '%LOG%'"
findstr /i /c:"No matching distribution" "%LOG%" >nul && call :say "  - Hint: this Python version has no wheel for one of the packages (use 3.9 - 3.11, 64-bit, or run without --use-system-python)."
findstr /i /c:"No such file or directory" /c:"path too long" "%LOG%" >nul && call :say "  - Hint: Windows 260-character path limit. Move JUN_JALI to a shorter path (e.g. C:\JUN_JALI)."
findstr /i /c:"SSL" /c:"timed out" /c:"ProxyError" "%LOG%" >nul && call :say "  - Hint: network / proxy problem. Check the internet connection or set a pip proxy."
goto :end_fail

:end_fail
call :say ""
call :say "SETUP FAILED - full log: %LOG%"
if "%NOPAUSE%"=="0" pause
exit /b 1

rem ---------------------------------------------------------------------------
:parse_model
if "%~1"=="" exit /b 0
if /i "%~1"=="--model" (
    set "MODEL2=%~2"
    exit /b 0
)
shift
goto :parse_model

:get_model
rem %~1 = model name or HF repo -> models\hub. Exit code 1 on failure (download_model.py prints the reason).
"%VPY%" "tools\STT_Converter\download_model.py" "%~1" "%MODELS%\hub" > "%TEMP%\jun_jali_stt_dl.txt" 2>> "%LOG%"
set "DLRC=%ERRORLEVEL%"
type "%TEMP%\jun_jali_stt_dl.txt"
type "%TEMP%\jun_jali_stt_dl.txt" >> "%LOG%"
if not "%DLRC%"=="0" exit /b 1
exit /b 0

:env_summary
rem OS build / GPU / driver at the top of the log - the reference PC sends this log back (docs/0130 Q8)
for /f "tokens=*" %%V in ('ver') do >> "%LOG%" echo os: %%V
where nvidia-smi >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%G in ('nvidia-smi --query-gpu^=name^,driver_version^,memory.total --format^=csv^,noheader 2^>nul') do (
        >> "%LOG%" echo gpu: %%G
        call :say " GPU: %%G"
    )
) else (
    >> "%LOG%" echo gpu: nvidia-smi not found - no NVIDIA driver, CPU mode
    call :say " GPU: no NVIDIA driver found - the converter will run on the CPU (slower, still works)"
)
if exist "tools\STT_Converter\data\force_cpu.flag" call :say " Note: data\force_cpu.flag exists - CUDA is disabled on this PC"
exit /b 0

:find_python
rem D14 order: the private copy first (shared with setup_env.bat), then the PC (unless --no-system-python)
if exist "%PRIV_PY%" call :try_path "%PRIV_PY%"
if defined PY exit /b 0
if "%NOSYS%"=="1" exit /b 0
rem py launcher (3.11 -> 3.10 -> 3.9). Exit codes are not trusted - see the header.
for %%V in (3.11 3.10 3.9) do (
    if not defined PY call :try_cmd "py -%%V"
)
if "%USESYS%"=="1" for %%V in (3.12 3.13 3.14) do (
    if not defined PY call :try_cmd "py -%%V"
)
if defined PY exit /b 0
rem python on PATH - skip the Microsoft Store shortcut (WindowsApps)
for /f "delims=" %%P in ('where python 2^>nul') do (
    if not defined PY call :try_path "%%P"
)
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
if errorlevel 1 set "OTHERS=%OTHERS% Found Python %~1 (not supported - add --use-system-python to try it)."
exit /b 0

:probe
rem Runs the interpreter and reads what it prints. Sets P_VER (e.g. 3.14) and P_OK (3.9 - 3.11, 64-bit;
rem with --use-system-python also 3.12 - 3.14).  %~1 = "py -3.11" (command) or a full path to python.exe
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
            if "%USESYS%"=="1" (
                if "%%c"=="12" set "P_OK=1"
                if "%%c"=="13" set "P_OK=1"
                if "%%c"=="14" set "P_OK=1"
            )
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
    call :say "[ERROR] Download / extract failed - see setup_stt.log"
    call :say "        Network or proxy problem, or the folder path is too long (move JUN_JALI to e.g. C:\JUN_JALI)."
    exit /b 1
)
rmdir /s /q "%~dp0.python_dl"
if not exist "%PRIV_PY%" (
    call :say "[ERROR] The downloaded package has no python.exe - see setup_stt.log"
    exit /b 1
)
call :say "      private Python 3.11.9 is in .python\"
exit /b 0

:say
echo(%~1
>> "%LOG%" echo(%~1
exit /b 0
