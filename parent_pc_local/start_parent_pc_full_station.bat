@echo off
setlocal
cd /d "%~dp0\.."
if not exist ".venv\Scripts\python.exe" (
  echo Parent PC environment not found.
  echo Run parent_pc_local\setup_and_start.bat first.
  pause
  exit /b 1
)
echo Starting Parent PC local API...
start "Hearlium Parent PC API" cmd /k ".venv\Scripts\python.exe parent_pc_local\start_parent_pc_server.py"
timeout /t 2 /nobreak >nul
set "BTEXE=parent_pc_local\bluetooth_service\bin\Release\net8.0-windows10.0.19041.0\win-x64\publish\HearliumBluetoothService.exe"
if exist "%BTEXE%" start "Hearlium Bluetooth" "%BTEXE%"
start "Hearlium Parent PC Recording" ".venv\Scripts\pythonw.exe" parent_pc_local\direct_recording.py
