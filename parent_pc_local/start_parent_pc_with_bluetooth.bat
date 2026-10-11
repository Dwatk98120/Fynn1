@echo off
setlocal
cd /d "%~dp0\.."
echo Starting Hearlium Parent PC API...
start "Hearlium Parent PC API" cmd /k ".venv\Scripts\python.exe parent_pc_local\start_parent_pc_server.py"
timeout /t 2 /nobreak >nul
set "BTEXE=parent_pc_local\bluetooth_service\bin\Release\net8.0-windows10.0.19041.0\win-x64\publish\HearliumBluetoothService.exe"
if exist "%BTEXE%" (
  echo Starting Bluetooth handshake service...
  start "Hearlium Bluetooth" "%BTEXE%"
) else (
  echo Bluetooth helper has not been built yet.
  echo Run parent_pc_local\build_bluetooth_service.bat first.
)
echo.
echo Parent PC startup complete.
pause
