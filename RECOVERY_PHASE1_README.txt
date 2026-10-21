Hearlium Branch 2 — Recovery Phase 1 (2026-10-21)

SOURCE: Hearlium_Branch2_One_Tap_Caregiver_Review_Fix_20261020(3).zip

CHANGES:
- Parent PC server launcher avoids Uvicorn default console formatter when built as a windowed PyInstaller executable. Server logging goes to %LOCALAPPDATA%\Hearlium\ParentPC\parent_pc_server.log.
- Installer [Files] explicitly copies contents of dist\HearliumParentPC, preserving _internal and executables at {app} root.

IMPORTANT: Use BUILD_HEARLIUM_INSTALLER.bat in THIS ZIP's root, not a separate stale installer script. Its spec produces dist\HearliumParentPC\HearliumParentPC.exe. If you have a flat dist layout instead, don't compile this script against that output; run the batch builder or ask for flat-layout installer variant.

NOT YET INCLUDED: Later English-first ranking / Android response tracing / individual-word improvements. These will be selectively merged after this stable launch baseline is tested.

NOT VERIFIED: Windows PyInstaller compile, installer execution, actual speech recognition. Do not overwrite working installation or delete recordings. Keep Main frozen.

VISUAL C++: This phase retains the baseline redistributable behavior; conditional detection and failure/reboot handling remain a separate required fix before broad deployment.
