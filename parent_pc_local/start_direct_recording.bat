@echo off
setlocal
cd /d "%~dp0\.."
if not exist ".venv\Scripts\python.exe" (
  echo Parent PC environment not found.
  echo Run parent_pc_local\setup_and_start.bat first.
  pause
  exit /b 1
)
start "Hearlium Parent PC Recording" ".venv\Scripts\pythonw.exe" parent_pc_local\direct_recording.py
