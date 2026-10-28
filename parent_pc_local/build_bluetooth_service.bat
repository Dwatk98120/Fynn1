@echo off
setlocal
cd /d "%~dp0bluetooth_service"
where dotnet >nul 2>&1
if errorlevel 1 (
  echo .NET 8 SDK was not found. Install the .NET 8 SDK to build the Bluetooth service.
  pause
  exit /b 1
)
dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true
if errorlevel 1 (
  echo Bluetooth service build failed.
  pause
  exit /b 1
)
echo.
echo Build complete. The service is under bluetooth_service\bin\Release\net8.0-windows10.0.22000.0\win-x64\publish\
pause
