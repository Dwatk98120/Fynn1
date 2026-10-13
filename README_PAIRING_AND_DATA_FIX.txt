Hearlium Parent PC 0.3.1 - pairing and writable data hotfix

Fixed:
- Direct Recording no longer creates recordings, analysis_results, or config under Program Files.
- Pair Phone no longer demands setup_and_start.bat or a developer Python .venv in installed builds.
- Pair Phone reuses a healthy running server, or starts the frozen --server process.
- Bluetooth service is discovered alongside HearliumParentPC.exe when installed.
- Data directory: %LOCALAPPDATA%\Hearlium\ParentPC

Build on Windows: run BUILD_HEARLIUM_INSTALLER.bat and install installer\output\HearliumSetup.exe.
The installer builder compiles the Windows EXE; this ZIP is not a precompiled EXE.

Existing data under a previous installation is not deleted. If older recordings exist under the development source folder, copy them manually into the new data directory after backup.

Static Python compilation was checked. Windows compilation and Bluetooth runtime pairing still require verification on the user's Windows PC.
