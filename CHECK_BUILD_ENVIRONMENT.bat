@echo off
setlocal
cd /d "%~dp0"

echo Hearlium Windows Build Environment Check
echo ========================================
echo.

py -3.12 --version
if errorlevel 1 (
  echo FAIL: Python 3.12 not found.
  pause
  exit /b 1
)

if not exist ".installer_venv\Scripts\python.exe" (
  echo NOTE: .installer_venv has not been created yet.
  echo Run BUILD_HEARLIUM_INSTALLER.bat first.
  pause
  exit /b 0
)

".installer_venv\Scripts\python.exe" -m pip --version
".installer_venv\Scripts\python.exe" -c "import sys; print('Python:',sys.version)"
".installer_venv\Scripts\python.exe" -c "import fastapi, uvicorn; print('FastAPI/Uvicorn: OK')"
".installer_venv\Scripts\python.exe" -c "from g2p_en import G2p; print('g2p-en: OK')"

if exist "dist\HearliumParentPC\HearliumParentPC.exe" (
  echo Parent PC EXE: FOUND
) else (
  echo Parent PC EXE: NOT BUILT YET
)

if exist "installer\output\HearliumSetup.exe" (
  echo Installer EXE: FOUND
) else (
  echo Installer EXE: NOT BUILT YET
)

echo.
pause
