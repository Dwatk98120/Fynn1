# Hearlium frozen launcher self-test repair — 2026-10-18

Fixes the PyInstaller frozen executable failure:
`ValueError: no signature found for builtin <built-in function open>`.

The launcher self-test now decodes a short in-memory WAV through
`av.open(..., metadata_errors="ignore")` instead of calling
`inspect.signature(av.open)`.

All other files from the supplied combined repair ZIP are retained unchanged.

Run `BUILD_HEARLIUM_INSTALLER.bat` from the extracted project root.
The frozen self-test must pass before the Inno Setup installer stage.

Validation performed here: Python syntax compilation and ZIP integrity.
Windows frozen executable and installer still require a build on Windows.
