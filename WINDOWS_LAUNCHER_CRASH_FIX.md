# Windows launcher crash fix

Fixed `AttributeError: NoneType has no attribute isatty` / `Unable to configure formatter default` when running a PyInstaller windowed executable.

`parent_pc_local/hearlium_launcher.py` now calls `uvicorn.run(..., log_config=None)` and records server errors in `%LOCALAPPDATA%\Hearlium\ParentPC\hearlium_server.log`.

This ZIP is the installer **builder source**, not a precompiled Windows installer. On Windows, extract into a new directory and run `BUILD_HEARLIUM_INSTALLER.bat`, then install the newly generated installer. Close any existing Hearlium instances first.

Validation: Python syntax compiled. Windows build and runtime not verified in this environment.
