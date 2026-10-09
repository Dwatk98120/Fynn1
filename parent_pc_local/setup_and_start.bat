@echo off
setlocal
cd /d "%~dp0\.."

echo ============================================================
echo First Sound Helper / Hearlium Parent PC Local Backend
echo ============================================================
echo.

if not exist ".venv\Scripts\python.exe" (
  echo Creating local Python environment...
  py -3 -m venv .venv
  if errorlevel 1 (
    echo Python 3 was not found. This Phase 1 launcher requires Python 3.
    pause
    exit /b 1
  )
)

call ".venv\Scripts\activate.bat"

echo Installing/updating server requirements...
python -m pip install --upgrade pip
pip install -r server\requirements.txt
if errorlevel 1 (
  echo.
  echo Dependency installation failed.
  pause
  exit /b 1
)

echo.
echo Starting Parent PC local backend...
python parent_pc_local\start_parent_pc_server.py
pause
