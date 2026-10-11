@echo off
setlocal
cd /d "%~dp0\.."
if not exist ".venv\Scripts\pythonw.exe" (
  echo Parent PC setup has not been completed yet.
  echo Run parent_pc_local\setup_and_start.bat first.
  pause
  exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" parent_pc_local\pair_phone.py
