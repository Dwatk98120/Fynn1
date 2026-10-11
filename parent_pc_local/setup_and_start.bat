@echo off
setlocal EnableExtensions
cd /d "%~dp0\.."

echo ============================================================
echo First Sound Helper / Hearlium Parent PC Local Backend
echo ============================================================
echo.

echo Checking for Python 3.12...
py -3.12 --version >nul 2>&1
if errorlevel 1 (
  echo.
  echo Python 3.12 was not found.
  echo This Parent PC build requires Python 3.12 for compatible Torch support.
  echo.
  echo Install Python 3.12.x, then run this file again.
  pause
  exit /b 1
)

set "RECREATE_VENV=0"

if exist ".venv\Scripts\python.exe" (
  for /f "tokens=2" %%V in ('".venv\Scripts\python.exe" --version 2^>^&1') do set "VENV_VERSION=%%V"

  echo Existing local environment detected: Python %VENV_VERSION%

  echo %VENV_VERSION% | findstr /b "3.12." >nul
  if errorlevel 1 (
    echo.
    echo Existing .venv is not Python 3.12.
    echo Rebuilding the environment with Python 3.12...
    set "RECREATE_VENV=1"
  )
) else (
  set "RECREATE_VENV=1"
)

if "%RECREATE_VENV%"=="1" (
  if exist ".venv" (
    rmdir /s /q ".venv"
    if exist ".venv" (
      echo.
      echo Could not remove the old .venv folder.
      echo Close any program using it and try again.
      pause
      exit /b 1
    )
  )

  echo Creating local Python 3.12 environment...
  py -3.12 -m venv .venv
  if errorlevel 1 (
    echo.
    echo Failed to create the Python 3.12 environment.
    pause
    exit /b 1
  )
)

call ".venv\Scripts\activate.bat"

echo.
echo Environment ready:
python --version

echo.
echo Installing/updating server requirements...
python -m pip install --upgrade pip
if errorlevel 1 (
  echo.
  echo Pip upgrade failed.
  pause
  exit /b 1
)

python -m pip install -r server\requirements.txt
if errorlevel 1 (
  echo.
  echo Dependency installation failed.
  echo Confirm this environment reports Python 3.12.x above.
  pause
  exit /b 1
)

echo.
echo Starting Parent PC local backend...
python parent_pc_local\start_parent_pc_server.py

echo.
echo Parent PC backend stopped.
pause
