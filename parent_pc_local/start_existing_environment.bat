@echo off
cd /d "%~dp0\.."
if exist ".venv\Scripts\python.exe" (
  call ".venv\Scripts\activate.bat"
)
python parent_pc_local\start_parent_pc_server.py
pause
