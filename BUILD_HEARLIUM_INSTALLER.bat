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

REM Attempt to install runtime on the BUILD computer as well. Torch needs it
REM during import verification. Administrator permission may be requested.
echo.
echo Installing or repairing Microsoft Visual C++ x64 runtime on this PC...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p=(Resolve-Path 'installer\prereqs\vc_redist.x64.exe').Path; Start-Process -FilePath $p -ArgumentList '/install /passive /norestart' -Verb RunAs -Wait"
if errorlevel 1 (
  echo.
  echo WARNING: Could not confirm VC++ runtime installation.
  echo If Torch reports a c10.dll error, install vc_redist.x64.exe manually.
  echo.
)

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

REM ------------------------------------------------------------
REM 3. Initialize pip without forcing a risky global upgrade
REM ------------------------------------------------------------
echo Initializing pip...
python -m ensurepip --upgrade
if errorlevel 1 goto :pipfail

python -m pip --version
if errorlevel 1 goto :pipfail

REM Use known-stable packaging tools for older speech dependencies.
echo Installing stable packaging tools...
python -m pip install --upgrade "pip==25.2" "setuptools==75.8.2" "wheel==0.45.1" "packaging==24.2"
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

call :install "NumPy" "numpy>=1.26,<3"
if errorlevel 1 exit /b 1

call :install "SoundFile" "soundfile>=0.12"
if errorlevel 1 exit /b 1

call :install "SoundDevice" "sounddevice>=0.5.0"
if errorlevel 1 exit /b 1

call :install "Requests" "requests>=2.32"
if errorlevel 1 exit /b 1

call :install "Transformers" "transformers>=4.48,<6"
if errorlevel 1 exit /b 1

call :install "Torch" "torch>=2.4"
if errorlevel 1 exit /b 1

REM g2p-en pulls in an old 'distance' package that can fail to build with
REM newer packaging metadata. Install the known dependencies explicitly.
call :install "NLTK" "nltk>=3.2.4"
if errorlevel 1 exit /b 1

call :install "Inflect" "inflect>=0.3.1"
if errorlevel 1 exit /b 1

REM The distance project is pure Python. Install it without PEP517 isolation
REM to avoid the temporary build environment that produced InvalidVersion 0.dev0.
echo.
echo Installing distance compatibility dependency...
python -m pip install --no-build-isolation --no-use-pep517 "distance==0.1.3"
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
python -m pip install --only-binary=g2p-en --no-deps "g2p-en==2.1.0"
if errorlevel 1 (
  echo.
  echo ERROR: g2p-en wheel installation failed.
  echo.
  pause
  exit /b 1
)

REM ------------------------------------------------------------
REM Speech recognition dependencies verified on Windows Python 3.12.
REM PyAV 19 produced: unexpected keyword argument metadata_errors.
REM Pin the tested PyAV 16.1.0 and verify the audio decoder API.
REM ------------------------------------------------------------
call :install "Faster-Whisper" "faster-whisper>=1.1,<2"
if errorlevel 1 exit /b 1
call :install "PyAV tested decoder" "av==16.1.0"
if errorlevel 1 exit /b 1

echo Checking dependency consistency...
python -m pip check
if errorlevel 1 goto :depfail

echo Checking PortAudio, Whisper and PyAV decoder API...
python -c "import av, sounddevice, soundfile; from faster_whisper import WhisperModel; import inspect; assert av.__version__ == '16.1.0', av.__version__; assert 'metadata_errors' in inspect.signature(av.open).parameters; print('PortAudio, Faster-Whisper and PyAV 16.1.0: OK')"
if errorlevel 1 goto :depfail

REM Validate the critical imports before building.
echo.
echo Verifying installed runtime packages...
python -c "import fastapi, uvicorn, multipart, numpy, soundfile, sounddevice, requests, transformers, torch; from g2p_en import G2p; from faster_whisper import WhisperModel; import av; print('Dependency import check: OK')"
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
pyinstaller --noconfirm --clean HearliumParentPC.spec
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
"%ISCC%" installer\Hearlium.iss
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
python -m pip install "%~2"
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
echo ERROR: Stable packaging tools could not be installed.
pause
exit /b 1
