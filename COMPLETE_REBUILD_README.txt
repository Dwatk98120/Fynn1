HEARLIUM PARENT PC — COMPLETE REBUILD

1. Right-click this ZIP -> Extract All (do not run from inside the ZIP).
2. Open the extracted Hearlium_Complete_Rebuild folder.
3. Confirm HearliumParentPC.spec, BUILD_HEARLIUM_INSTALLER.bat, parent_pc_local and installer are visible together.
4. Double-click BUILD_HEARLIUM_INSTALLER.bat. Python 3.12 and Inno Setup 6 are needed.
5. Bluetooth: dotnet SDK with .NET 8 Windows targeting support is needed; the build continues without it but clearly warns.
6. After BUILD COMPLETE install installer\output\HearliumSetup.exe.
7. If the server fails, inspect %%LOCALAPPDATA%%\Hearlium\ParentPC\hearlium_server.log.

This ZIP contains SOURCE and the Windows installer builder, not a precompiled Windows EXE.
Windows PyInstaller/Inno Setup compilation must be performed on Windows.
Preserves temporal prosody, 500 error fix, and Uvicorn windowed logging fix.
