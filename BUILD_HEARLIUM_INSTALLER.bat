@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ============================================================
echo Hearlium Parent PC - Windows Installer Builder v2
echo ============================================================
echo.

REM ------------------------------------------------------------
REM 1. Verify Python 3.12
REM ------------------------------------------------------------
py -3.12 --version >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python 3.12 was not found.
  echo Install Python 3.12, then run this file again.
  pause
  exit /b 1
)

REM Regression tests run inside the clean build environment below, after
REM its NumPy and pytest dependencies have been installed.  Do not require
REM separate pytest/NumPy installations in the user's global Python.

REM ------------------------------------------------------------
REM 1b. Bundle Microsoft Visual C++ x64 runtime prerequisite.
REM ------------------------------------------------------------
echo.
echo Downloading Microsoft Visual C++ runtime prerequisite...
if not exist "installer\prereqs" mkdir "installer\prereqs"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile 'installer\prereqs\vc_redist.x64.exe'"
if errorlevel 1 (
  echo.
  echo ERROR: Could not download Microsoft Visual C++ x64 runtime.
  echo The installer cannot be built without this prerequisite.
  pause
  exit /b 1
)
if not exist "installer\prereqs\vc_redist.x64.exe" (
  echo ERROR: Visual C++ prerequisite file is missing.
  pause
  exit /b 1
)

REM Never elevate/install prerequisites on the BUILD computer automatically.
echo VC++ redistributable staged for the final installer.

REM ------------------------------------------------------------
REM 2. Recreate clean build environment
REM ------------------------------------------------------------
if exist ".installer_venv" (
  echo Removing old installer environment...
  rmdir /s /q ".installer_venv"
)

echo Creating clean Python 3.12 environment...
py -3.12 -m venv .installer_venv
if errorlevel 1 (
  echo ERROR: Could not create .installer_venv
  pause
  exit /b 1
)

call ".installer_venv\Scripts\activate.bat"
REM Use the isolated interpreter by explicit path, not a potentially stale
REM python/pip/pyinstaller entry on the Windows PATH.
set "HEARLIUM_TEST_PYTHON=%CD%\.installer_venv\Scripts\python.exe"
if not exist "%HEARLIUM_TEST_PYTHON%" (
  echo ERROR: Isolated installer Python is missing.
  goto :pipfail
)
echo Installer Python: "%HEARLIUM_TEST_PYTHON%"

REM ------------------------------------------------------------
REM 3. Initialize pip without forcing a risky global upgrade
REM ------------------------------------------------------------
echo Initializing pip...
"%HEARLIUM_TEST_PYTHON%" -m ensurepip --upgrade
if errorlevel 1 goto :pipfail

"%HEARLIUM_TEST_PYTHON%" -m pip --version
if errorlevel 1 goto :pipfail

REM Use known-stable packaging tools for older speech dependencies.
echo Installing stable packaging tools...
"%HEARLIUM_TEST_PYTHON%" -m pip install --upgrade "pip==25.2" "setuptools==75.8.2" "wheel==0.45.1" "packaging==24.2"
if errorlevel 1 goto :depfail

REM ------------------------------------------------------------
REM 4. Install build tool first
REM ------------------------------------------------------------
call :install "PyInstaller" "pyinstaller==6.16.0"
if errorlevel 1 exit /b 1

REM ------------------------------------------------------------
REM 5. Install application dependencies one by one
REM This makes failures easy to identify.
REM ------------------------------------------------------------
call :install "FastAPI" "fastapi==0.115.6"
if errorlevel 1 exit /b 1

call :install "Uvicorn" "uvicorn[standard]==0.34.0"
if errorlevel 1 exit /b 1

call :install "python-multipart" "python-multipart==0.0.20"
if errorlevel 1 exit /b 1

call :install "NumPy" "numpy==1.26.4"
if errorlevel 1 exit /b 1

call :install "SoundFile" "soundfile==0.13.1"
if errorlevel 1 exit /b 1

call :install "SoundDevice" "sounddevice==0.5.2"
if errorlevel 1 exit /b 1

call :install "Requests" "requests==2.32.3"
if errorlevel 1 exit /b 1

call :install "Transformers" "transformers==4.49.0"
if errorlevel 1 exit /b 1

call :install "Torch" "torch==2.6.0"
if errorlevel 1 exit /b 1

REM Silero's official Python wheel contains the offline TorchScript VAD model.
REM No torch.hub runtime downloads are allowed on an installed Parent PC.
call :install "Silero VAD (offline Layer 2 model)" "silero-vad==6.2.3"
if errorlevel 1 exit /b 1

REM g2p-en pulls in an old 'distance' package that can fail to build with
REM newer packaging metadata. Install the known dependencies explicitly.
call :install "NLTK" "nltk==3.9.1"
if errorlevel 1 exit /b 1

call :install "Inflect" "inflect==7.5.0"
if errorlevel 1 exit /b 1

REM The distance project is pure Python. Install it without PEP517 isolation
REM to avoid the temporary build environment that produced InvalidVersion 0.dev0.
echo.
echo Installing distance compatibility dependency...
"%HEARLIUM_TEST_PYTHON%" -m pip install --no-build-isolation --no-use-pep517 "distance==0.1.3"
if errorlevel 1 (
  echo.
  echo ERROR: distance==0.1.3 failed to install.
  echo This package is required by g2p-en.
  echo.
  pause
  exit /b 1
)

REM Install g2p-en itself from the published wheel, and do not rebuild deps.
echo.
echo Installing g2p-en from wheel...
"%HEARLIUM_TEST_PYTHON%" -m pip install --only-binary=g2p-en --no-deps "g2p-en==2.1.0"
if errorlevel 1 (
  echo.
  echo ERROR: g2p-en wheel installation failed.
  echo.
  pause
  exit /b 1
)

REM ------------------------------------------------------------
REM ------------------------------------------------------------
REM Restore Faster-Whisper using binary wheels; never compile PyAV.
REM ------------------------------------------------------------
echo Installing pinned Faster-Whisper and native dependencies...
"%HEARLIUM_TEST_PYTHON%" -m pip install --only-binary=:all: -r server\requirements-word-asr.txt
if errorlevel 1 goto :depfail

REM Run ALL regressions (unittest and pytest function tests) in the isolated
REM environment. The original Phase 3 build only ran unittest discovery,
REM leaving the pytest-only tests unchecked.
echo Installing test runner into build environment...
"%HEARLIUM_TEST_PYTHON%" -m pip install "pytest==8.4.2"
if errorlevel 1 goto :depfail

REM Some Windows build runs have reported a successful earlier package
REM installation, but requests was no longer importable during test collection.
REM Verify using the EXACT interpreter that runs regression tests. Never
REM change global Python or silently continue if recovery fails.
echo Checking requests in the isolated installer/test environment...
"%HEARLIUM_TEST_PYTHON%" -c "import sys, requests; print('Test Python:', sys.executable); print('Requests:', requests.__version__)"
if errorlevel 1 (
  echo requests is unavailable in the regression-test interpreter.
  echo Attempting a one-time repair inside .installer_venv...
  "%HEARLIUM_TEST_PYTHON%" -m pip install --only-binary=:all: "requests==2.32.3"
  if errorlevel 1 goto :depfail
  "%HEARLIUM_TEST_PYTHON%" -c "import sys, requests; print('Recovered requests', requests.__version__, 'in', sys.executable)"
  if errorlevel 1 goto :depfail
)
echo Checking NLTK in the isolated installer/test environment...
"%HEARLIUM_TEST_PYTHON%" -c "import nltk; print('NLTK:', nltk.__version__)"
if errorlevel 1 (
  echo NLTK is unavailable in the regression-test interpreter.
  echo Attempting a one-time NLTK repair inside .installer_venv...
  "%HEARLIUM_TEST_PYTHON%" -m pip install --only-binary=:all: "nltk==3.9.1"
  if errorlevel 1 goto :depfail
  "%HEARLIUM_TEST_PYTHON%" -c "import nltk; print('Recovered NLTK:', nltk.__version__)"
  if errorlevel 1 goto :depfail
)
REM pip check alone does not detect omitted optional runtime imports such as
REM soundfile, sounddevice or silero_vad. Audit EVERY pinned direct runtime,
REM audio and build requirement before proceeding. Repair only inside this
REM disposable installer virtual environment; fail if any remains unavailable.
echo Auditing all pinned speech/audio/build Python dependencies...
"%HEARLIUM_TEST_PYTHON%" "installer\ensure_build_dependencies.py" --repair
if errorlevel 1 goto :depfail
echo Checking isolated Python dependency consistency before tests...
"%HEARLIUM_TEST_PYTHON%" -m pip check
if errorlevel 1 goto :depfail
echo Running full Phase 2 + Phase 3 + startup reliability regression suite...
"%HEARLIUM_TEST_PYTHON%" -m pytest -q server\tests
if errorlevel 1 (
  echo ERROR: Full regression suite failed. No installer will be created.
  pause
  exit /b 1
)
echo Regression suite passed.

echo Checking dependency consistency...
"%HEARLIUM_TEST_PYTHON%" -m pip check
if errorlevel 1 goto :depfail
"%HEARLIUM_TEST_PYTHON%" -m pip freeze > installer\resolved-dependencies.txt

echo Checking native PyAV and Faster-Whisper dependencies...
"%HEARLIUM_TEST_PYTHON%" "installer\verify_audio_dependencies.py"
if errorlevel 1 goto :depfail

REM Ensure the actual Silero model executes before packaging. This checks
REM more than importability and fails this build on a missing model asset.
echo Checking offline Silero VAD inference...
"%HEARLIUM_TEST_PYTHON%" "installer\verify_silero_vad.py"
if errorlevel 1 goto :depfail

REM Download and validate the actual offline model before freezing.
"%HEARLIUM_TEST_PYTHON%" "installer\prepare_whisper_model.py"
if errorlevel 1 goto :depfail

REM Stage the phoneme CTC model INSIDE the installer, too. Only the build PC
REM may download; installed Parent PCs analyze offline without Wi-Fi.
echo Preparing independent phoneme model for offline installation...
"%HEARLIUM_TEST_PYTHON%" "installer\prepare_phoneme_model.py"
if errorlevel 1 (
  echo ERROR: Phoneme model download or staging failed. Installer not built.
  echo Free adequate disk space and verify internet on BUILD computer.
  pause
  exit /b 1
)


REM Validate the critical imports before building.
echo.
echo Verifying installed runtime packages...
"%HEARLIUM_TEST_PYTHON%" -c "import fastapi, uvicorn, multipart, numpy, soundfile, sounddevice, requests, nltk, transformers, torch, av, ctranslate2, faster_whisper, silero_vad; from g2p_en import G2p; print('Dependency import check: OK')"
if errorlevel 1 (
  echo.
  echo ERROR: One or more runtime imports failed.
  echo The installer build will not continue.
  pause
  exit /b 1
)

REM ------------------------------------------------------------
REM 6. Bluetooth helper (required)
REM ------------------------------------------------------------
echo.
echo Checking Windows Bluetooth helper (.NET 8 SDK required)...
where dotnet >nul 2>&1
if errorlevel 1 (
  echo ERROR: dotnet SDK not found. Install .NET 8 SDK x64.
  pause
  exit /b 1
)
dotnet --list-sdks | findstr /R /C:"^8\." >nul
if errorlevel 1 (
  echo ERROR: .NET 8 SDK not found. Install .NET 8 SDK x64.
  pause
  exit /b 1
)
set "BTEXE=parent_pc_local\bluetooth_service\bin\Release\net8.0-windows10.0.22000.0\win-x64\publish\HearliumBluetoothService.exe"
if exist "!BTEXE!" del /F /Q "!BTEXE!"
dotnet publish "parent_pc_local\bluetooth_service\HearliumBluetoothService.csproj" -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true
if errorlevel 1 (
  echo ERROR: Bluetooth helper build failed. Installer aborted.
  pause
  exit /b 1
)
if not exist "!BTEXE!" (
  echo ERROR: Bluetooth helper EXE not produced. Installer aborted.
  pause
  exit /b 1
)

REM ------------------------------------------------------------
REM ------------------------------------------------------------
REM 7. Clean old PyInstaller output and build
REM ------------------------------------------------------------
echo.
echo Cleaning previous PyInstaller output...
if exist "build" rmdir /s /q "build"
if exist "dist\HearliumParentPC" rmdir /s /q "dist\HearliumParentPC"

echo.
echo Building Hearlium Parent PC executable...
"%HEARLIUM_TEST_PYTHON%" -m PyInstaller --noconfirm --clean HearliumParentPC.spec
if errorlevel 1 (
  echo.
  echo ERROR: PyInstaller build failed.
  pause
  exit /b 1
)

REM Hard stop if expected executable does not exist.
if not exist "dist\HearliumParentPC\HearliumParentPC.exe" (
  echo.
  echo ERROR: PyInstaller finished but the expected executable was not created:
  echo        dist\HearliumParentPC\HearliumParentPC.exe
  echo.
  echo Inno Setup will NOT be started.
  pause
  exit /b 1
)

REM Copy required Bluetooth helper into the frozen application folder.
echo Copying required Bluetooth helper into distribution...
copy /Y "!BTEXE!" "dist\HearliumParentPC\HearliumBluetoothService.exe" >nul
if errorlevel 1 (
  echo ERROR: Failed to copy Bluetooth helper. Installer aborted.
  pause
  exit /b 1
)
if not exist "dist\HearliumParentPC\HearliumBluetoothService.exe" (
  echo ERROR: Bluetooth helper missing from distribution.
  pause
  exit /b 1
)

echo.
echo SUCCESS: Parent PC executable created:
echo dist\HearliumParentPC\HearliumParentPC.exe

REM ------------------------------------------------------------
REM 7a. Verify frozen executable imports before packaging.
REM ------------------------------------------------------------
echo.
echo Checking frozen application imports...
"dist\HearliumParentPC\HearliumParentPC.exe" --self-test
if errorlevel 1 (
  echo ERROR: Frozen application import check failed.
  pause
  exit /b 1
)

REM Critically, confirm that the freshly frozen EXE itself (not just the
REM Python sources) contains the Layer 2 evidence fix. Exit code is used
REM because Windows GUI executables do not reliably show console output.
echo Checking Layer 2 code inside newly built executable...
"dist\HearliumParentPC\HearliumParentPC.exe" --verify-layer2
if errorlevel 1 (
  echo ERROR: Frozen EXE is missing new Layer 2 activity evidence.
  echo Installer will not be created from an old or incomplete executable.
  pause
  exit /b 1
)
py -3.12 "installer\verify_layer2_build.py" stamp
if errorlevel 1 (
  echo ERROR: Could not stamp verified executable and source.
  pause
  exit /b 1
)

REM ------------------------------------------------------------
REM 8. Locate Inno Setup compiler
REM ------------------------------------------------------------
echo.
echo Locating Inno Setup compiler...
set "ISCC="

if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if not defined ISCC (
  where iscc >nul 2>&1
  if not errorlevel 1 set "ISCC=iscc"
)

if not defined ISCC (
  echo.
  echo HearliumParentPC.exe was built successfully.
  echo Inno Setup 6 was not found, so HearliumSetup.exe was not created.
  echo.
  echo Install Inno Setup 6 and rerun this same file.
  echo Existing app build:
  echo dist\HearliumParentPC\
  pause
  exit /b 1
)

REM ------------------------------------------------------------
REM 9. Build installer
REM ------------------------------------------------------------
echo.
echo Building HearliumSetup.exe...
call "COMPILE_INSTALLER_ONLY.bat"
if errorlevel 1 (
  echo.
  echo ERROR: Inno Setup compilation failed.
  echo Parent PC executable is still available at:
  echo dist\HearliumParentPC\HearliumParentPC.exe
  pause
  exit /b 1
)

if not exist "installer\output\HearliumSetup.exe" (
  echo.
  echo ERROR: Inno Setup completed but HearliumSetup.exe was not found.
  pause
  exit /b 1
)

echo.
echo ============================================================
echo BUILD COMPLETE
echo ============================================================
echo.
echo Your Windows installer is:
echo installer\output\HearliumSetup.exe
echo.
echo You can now install Hearlium Parent PC by double-clicking that file.
echo.
pause
exit /b 0

:install
REM Package spec MUST remain quoted because Windows CMD treats > and < as redirection.
echo.
echo Installing %~1...
"%HEARLIUM_TEST_PYTHON%" -m pip install "%~2"
if errorlevel 1 (
  echo.
  echo ERROR: %~1 failed to install.
  echo Package: %~2
  echo.
  pause
  exit /b 1
)
exit /b 0

:pipfail
echo.
echo ERROR: pip could not be initialized correctly.
pause
exit /b 1

:depfail
echo.
echo ERROR: Build dependency installation or verification failed.
pause
exit /b 1
