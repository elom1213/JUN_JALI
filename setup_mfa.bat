@echo off
rem ============================================================================
rem  JUN_JALI - Montreal Forced Aligner (MFA) setup  (double-click to run)
rem  Python Script by Ji Hun Park / last Update date : 2026-10-20
rem
rem  Optional: only the "Correct" mode of the converter (WAV + transcript) needs MFA.
rem  Everything goes into ONE folder you choose (default: .mfa\ in this repository):
rem     <folder>\miniforge\   conda (Miniforge, private - PATH / registry are not touched)
rem     <folder>\env\         the MFA environment
rem     <folder>\models\      MFA_ROOT_DIR - acoustic models, dictionaries, MFA temp files
rem  Delete the folder to uninstall. The chosen folder is saved in mfa_path.local.txt
rem  (gitignored) - the converter reads it.
rem
rem  1) choose the folder (argument / prompt / Enter = default). No spaces, ASCII only:
rem     conda and Kaldi fail on such paths (e.g. a Korean Windows user name).
rem  2) Miniforge (SHA-256 checked, silent "just me" install)
rem  3) MFA environment - from mfa_env.lock.txt (exact versions of the first install) when
rem     it exists, otherwise from the pinned package list below
rem  4) models: english_mfa, korean_mfa, japanese_mfa (acoustic + dictionary) + G2P models
rem     (english_us_mfa, korean_mfa, japanese_mfa) for words that are not in the dictionary
rem  5) self test: aligns test_audio\coffee_xxxx.wav with its transcript
rem
rem  Usage:  setup_mfa.bat [folder] [--yes] [--nopause] [--force]
rem          --force rebuilds the environment (Miniforge and models are kept)
rem  Full output: setup_mfa.log
rem ============================================================================
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

set "LOG=%~dp0setup_mfa.log"
set "LOCK=%~dp0mfa_env.lock.txt"
set "PATHFILE=%~dp0mfa_path.local.txt"
set "MF_VER=26.7.2-0"
set "MF_EXE=Miniforge3-%MF_VER%-Windows-x86_64.exe"
set "MF_URL=https://github.com/conda-forge/miniforge/releases/download/%MF_VER%/%MF_EXE%"
set "MF_SHA=71cf9519087be74fa53021219ff292beb2fc05fa49e0bb6eb0e0b6b14fccbaab"
rem Pinned packages for a fresh environment (used only when mfa_env.lock.txt is missing).
rem Japanese needs sudachipy + sudachidict-core (MFA docs). Korean: python-mecab-ko (pip, requirements_mfa.txt).
set "MFA_PKGS=montreal-forced-aligner=3.4.3 python=3.11 sudachipy sudachidict-core"
set "MODELS=english_mfa korean_mfa japanese_mfa"
set "G2P_MODELS=english_us_mfa korean_mfa japanese_mfa"
set "MIN_FREE_GB=10"

set "ARG_DIR="
set "FORCE=0"
set "NOPAUSE=0"
set "YES=0"
for %%A in (%*) do (
    if /i "%%~A"=="--force" (set "FORCE=1") else if /i "%%~A"=="--nopause" (set "NOPAUSE=1") else if /i "%%~A"=="--yes" (set "YES=1") else set "ARG_DIR=%%~A"
)

> "%LOG%" echo JUN_JALI MFA setup - %DATE% %TIME%
call :say "============================================================"
call :say " JUN_JALI - Montreal Forced Aligner setup"
call :say " Repository: %CD%"
call :say "============================================================"

if not exist "test_audio\coffee_xxxx.wav" (
    call :say "[ERROR] test_audio\coffee_xxxx.wav not found - run this file from the JUN_JALI folder."
    goto :end_fail
)

rem ---------------------------------------------------------------- 1) folder
call :say ""
call :say "[1/5] Install folder"
set "DEF_DIR=%~dp0.mfa"
if exist "%PATHFILE%" set /p DEF_DIR=<"%PATHFILE%"
set "WANT=%ARG_DIR%"
if defined WANT goto :check_dir

:ask_dir
if "%YES%"=="1" (
    set "WANT=%DEF_DIR%"
    goto :check_dir
)
set "WANT="
set /p "WANT=      Install folder [%DEF_DIR%]: "
if not defined WANT set "WANT=%DEF_DIR%"

:check_dir
call :validate_dir "%WANT%"
if defined BAD (
    call :say "[ERROR] %BAD%"
    if defined ARG_DIR goto :end_fail
    if "%YES%"=="1" goto :end_fail
    call :say "        Choose another folder, e.g. C:\mfa"
    goto :ask_dir
)
set "ROOT=%OKDIR%"
set "MF=%ROOT%\miniforge"
set "ENV=%ROOT%\env"
set "MFA_ROOT_DIR=%ROOT%\models"
call :say "      folder: %ROOT%   (free %FREE_GB% GB)"
if not exist "%ROOT%" mkdir "%ROOT%"
if not exist "%MFA_ROOT_DIR%" mkdir "%MFA_ROOT_DIR%"

rem ---------------------------------------------------------------- 2) Miniforge
call :say ""
call :say "[2/5] Miniforge %MF_VER% ..."
if exist "%MF%\Scripts\conda.exe" (
    call :say "      reusing %MF%"
    goto :have_mf
)
if exist "%MF%" (
    call :say "      removing an incomplete Miniforge folder"
    rmdir /s /q "%MF%"
)
call :download_miniforge
if errorlevel 1 goto :end_fail
call :say "      installing (silent, just me, no PATH / registry changes) ..."
start "" /wait "%ROOT%\_dl\%MF_EXE%" /InstallationType=JustMe /RegisterPython=0 /AddToPath=0 /NoRegistry=1 /NoShortcuts=1 /S /D=%MF%
if not exist "%MF%\Scripts\conda.exe" (
    call :say "[ERROR] Miniforge install failed (no conda.exe in %MF%)"
    goto :end_fail
)
rmdir /s /q "%ROOT%\_dl" >nul 2>&1
call :say "      Miniforge OK"
:have_mf
set "CONDA=%MF%\Scripts\conda.exe"

rem ---------------------------------------------------------------- 3) environment
call :say ""
call :say "[3/5] MFA environment ..."
if "%FORCE%"=="1" if exist "%ENV%" (
    call :say "      --force: removing the old environment"
    rmdir /s /q "%ENV%"
)
if exist "%ENV%\Scripts\mfa.exe" (
    call :say "      reusing %ENV%"
    goto :env_extras
)
if exist "%ENV%" rmdir /s /q "%ENV%"
if exist "%LOCK%" (
    call :say "      from mfa_env.lock.txt (exact versions - first time: 5 - 15 minutes, about 6.5 GB) ..."
    "%CONDA%" create -y -p "%ENV%" --file "%LOCK%" >> "%LOG%" 2>&1
) else (
    call :say "      from the pinned package list (first time: 5 - 15 minutes, about 6.5 GB) ..."
    "%CONDA%" create -y -p "%ENV%" -c conda-forge --override-channels %MFA_PKGS% >> "%LOG%" 2>&1
)
if not exist "%ENV%\Scripts\mfa.exe" (
    call :say "[ERROR] Could not create the MFA environment. Last lines of setup_mfa.log:"
    powershell -NoProfile -Command "Get-Content -Tail 15 -LiteralPath '%LOG%'"
    findstr /i /c:"CondaHTTPError" /c:"SSL" /c:"timed out" /c:"ProxyError" "%LOG%" >nul && call :say "  - Hint: network / proxy problem."
    goto :end_fail
)
"%CONDA%" clean --tarballs --index-cache -y >> "%LOG%" 2>&1
:env_extras
rem Korean tokenizer for MFA (pip wheels; not on conda-forge). Same versions on every PC.
call :env_path
"%ENV%\python.exe" -c "import mecab" >nul 2>&1
if errorlevel 1 (
    call :say "      installing the Korean tokenizer (python-mecab-ko) ..."
    "%ENV%\python.exe" -m pip install --no-input -r "%~dp0requirements_mfa.txt" >> "%LOG%" 2>&1
    if errorlevel 1 (
        call :say "[ERROR] pip install -r requirements_mfa.txt failed - see setup_mfa.log"
        goto :end_fail
    )
)
call :mfa version > "%TEMP%\jun_jali_mfa_ver.txt" 2>> "%LOG%"
set "MFAVER="
set /p MFAVER=<"%TEMP%\jun_jali_mfa_ver.txt"
del "%TEMP%\jun_jali_mfa_ver.txt" >nul 2>&1
if not defined MFAVER (
    call :say "[ERROR] mfa does not run - see setup_mfa.log"
    goto :end_fail
)
call :say "      MFA %MFAVER% OK"

rem ---------------------------------------------------------------- 4) models
call :say ""
call :say "[4/5] Models (acoustic + dictionary): %MODELS% / G2P: %G2P_MODELS% ..."
for %%M in (%MODELS%) do (
    call :get_model acoustic %%M
    if errorlevel 1 goto :end_fail
    call :get_model dictionary %%M
    if errorlevel 1 goto :end_fail
)
for %%M in (%G2P_MODELS%) do (
    call :get_model g2p %%M
    if errorlevel 1 goto :end_fail
)

rem ---------------------------------------------------------------- 5) self test
call :say ""
call :say "[5/5] Self test (aligns test_audio\coffee_xxxx.wav) ..."
set "ST=%TEMP%\jun_jali_mfa_selftest"
if exist "%ST%" rmdir /s /q "%ST%"
mkdir "%ST%\in"
"%ENV%\python.exe" -c "import sys, soundfile as sf; d, r = sf.read(sys.argv[1], dtype='int16'); d = d.mean(axis=1).astype('int16') if d.ndim > 1 else d; sf.write(sys.argv[2], d, r, subtype='PCM_16')" "test_audio\coffee_xxxx.wav" "%ST%\in\coffee.wav" >> "%LOG%" 2>&1
> "%ST%\in\coffee.lab" echo This coffee sucks
call :mfa align "%ST%\in" english_mfa english_mfa "%ST%\out" --clean --single_speaker --quiet >> "%LOG%" 2>&1
if not exist "%ST%\out\coffee.TextGrid" (
    call :say "[ERROR] Self test failed (no TextGrid) - see setup_mfa.log"
    goto :end_fail
)
findstr /c:"\"phones\"" "%ST%\out\coffee.TextGrid" >nul || (
    call :say "[ERROR] Self test: the TextGrid has no phones tier - see setup_mfa.log"
    goto :end_fail
)
rmdir /s /q "%ST%" >nul 2>&1
call :say "      alignment OK"

> "%PATHFILE%" echo %ROOT%
if not exist "%LOCK%" (
    "%CONDA%" list -p "%ENV%" --explicit > "%LOCK%" 2>> "%LOG%"
    call :say "      wrote mfa_env.lock.txt (commit it - other PCs then get the same versions)"
)
call :say ""
call :say "============================================================"
call :say " MFA SETUP OK  -  %ROOT%"
call :say " The converter finds it through mfa_path.local.txt."
call :say "============================================================"
if "%NOPAUSE%"=="0" pause
exit /b 0

rem ============================================================================
:end_fail
call :say ""
call :say "MFA SETUP FAILED - full log: %LOG%"
if "%NOPAUSE%"=="0" pause
exit /b 1

rem ---------------------------------------------------------------------------
:validate_dir
rem Sets OKDIR (full path) + FREE_GB, or BAD (reason). The path goes through an environment
rem variable so quotes / special characters cannot break the PowerShell command.
set "BAD="
set "OKDIR="
set "FREE_GB="
set "JALI_DIR=%~1"
set "JALI_MIN=%MIN_FREE_GB%"
set "JALI_RES=%TEMP%\jun_jali_mfa_dir.txt"
rem (the PowerShell check writes one line to a file - braces / parentheses inside "for /f (...)" break cmd)
powershell -NoProfile -Command ^
  "$p=$env:JALI_DIR.Trim().Trim([char]34); try { $f=[IO.Path]::GetFullPath($p).TrimEnd([char]92) } catch { 'BAD|not a valid path: ' + $p; exit };" ^
  "if ($f -notmatch '^[A-Za-z]:\\') { 'BAD|use a full path on a local drive, e.g. C:\mfa: ' + $f; exit };" ^
  "if ($f -notmatch '^[\x21-\x7E]+$') { 'BAD|the folder path must not contain spaces or non-ASCII characters: ' + $f; exit };" ^
  "$free=[math]::Floor(([IO.DriveInfo]::new($f.Substring(0,3))).AvailableFreeSpace/1GB);" ^
  "if ($free -lt [int]$env:JALI_MIN) { 'BAD|only ' + $free + ' GB free on ' + $f.Substring(0,2) + ' - need ' + $env:JALI_MIN + ' GB'; exit };" ^
  "'OK|' + $f + '|' + $free" > "%JALI_RES%" 2>> "%LOG%"
for /f "usebackq tokens=1,* delims=|" %%a in ("%JALI_RES%") do (
    if "%%a"=="OK" (
        for /f "tokens=1,2 delims=|" %%x in ("%%b") do (
            set "OKDIR=%%x"
            set "FREE_GB=%%y"
        )
    ) else (
        set "BAD=%%b"
    )
)
del "%JALI_RES%" >nul 2>&1
if not defined OKDIR if not defined BAD set "BAD=could not check the folder: %~1"
exit /b 0

:download_miniforge
call :say "      downloading %MF_EXE% (about 150 MB) ..."
if exist "%ROOT%\_dl" rmdir /s /q "%ROOT%\_dl"
mkdir "%ROOT%\_dl"
set "JALI_OUT=%ROOT%\_dl\%MF_EXE%"
set "JALI_URL=%MF_URL%"
set "JALI_SHA=%MF_SHA%"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue';" ^
  "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;" ^
  "(New-Object Net.WebClient).DownloadFile($env:JALI_URL, $env:JALI_OUT);" ^
  "$s=[IO.File]::OpenRead($env:JALI_OUT); $h=-join ([Security.Cryptography.SHA256]::Create().ComputeHash($s) | ForEach-Object { $_.ToString('x2') }); $s.Close();" ^
  "if ($h -ne $env:JALI_SHA) { throw ('SHA-256 mismatch: ' + $h) };" ^
  "Write-Output 'download + SHA-256 OK'" >> "%LOG%" 2>&1
if errorlevel 1 (
    call :say "[ERROR] Miniforge download failed - see setup_mfa.log (network / proxy?)"
    exit /b 1
)
exit /b 0

:env_path
rem conda environments need their Library\bin folders on PATH (DLLs) - same as "conda activate".
set "PATH=%ENV%;%ENV%\Library\mingw-w64\bin;%ENV%\Library\usr\bin;%ENV%\Library\bin;%ENV%\Scripts;%ENV%\bin;%PATH%"
set "CONDA_PREFIX=%ENV%"
exit /b 0

:mfa
"%ENV%\Scripts\mfa.exe" %*
exit /b %ERRORLEVEL%

:get_model
rem %1 = acoustic | dictionary | g2p, %2 = model name. Skips models that are already downloaded.
rem Checked by file (not "mfa model inspect": in MFA 3.4.3 it crashes on dictionaries - AttributeError).
set "MODEL_FILE=%MFA_ROOT_DIR%\pretrained_models\%1\%2.zip"
if /i "%1"=="dictionary" set "MODEL_FILE=%MFA_ROOT_DIR%\pretrained_models\%1\%2.dict"
if exist "%MODEL_FILE%" (
    call :say "      %1 %2: present"
    exit /b 0
)
call :say "      %1 %2: downloading ..."
call :mfa model download %1 %2 >> "%LOG%" 2>&1
if not exist "%MODEL_FILE%" (
    call :say "[ERROR] could not download the %1 model %2 - see setup_mfa.log"
    exit /b 1
)
exit /b 0

:say
echo(%~1
>> "%LOG%" echo(%~1
exit /b 0
