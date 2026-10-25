# Hearlium Branch 2 — Windows Dependency Integrity Follow-up

## Evidence from the Windows build

On October 24, 2026, the full Windows installer builder recovered a missing
`requests==2.32.3` dependency and completed **237 tests passed, 3 skipped**.
It then failed `pip check` because `g2p-en==2.1.0` required NLTK, which was
absent. David installed `nltk==3.9.1` manually into `.installer_venv` and
verified **`No broken requirements found.`**

The earlier scripted installs included both packages; the reason they were
missing at later stages is still uncertain. The new checks enforce the
correct interpreter and dependency state instead of assuming pip success.

## Fix included

1. All Python package installation, model-preparation checks, runtime import
   tests, regression tests and PyInstaller use the **same explicit**
   `.installer_venv\Scripts\python.exe` rather than relying on PATH resolution.
2. Directly before regression tests, the builder verifies that both
   `requests` and `nltk` import. It repairs a missing package using its
   version-pinned wheel **inside that isolated build environment** and
   re-verifies imports; it stops if any recovery fails.
3. The builder runs `pip check` before and after the regression suite to
   identify any remaining broken requirements before model packaging.
4. The stop message describes dependency failure accurately. Additional
   regression tests guard these build-script requirements.
5. Main remains frozen. Android, original recordings, evidence histories,
   approval workflow, Silero Layer 2 code, phoneme engines and model versions
   have not been modified.

## Validation required on Windows

Extract this **complete source ZIP** into a new folder and run
`BUILD_HEARLIUM_INSTALLER.bat`. The builder will recreate its environment,
install its dependencies, check imports and dependencies, run the complete
pytest suite, verify the actual offline Silero model, build the frozen EXE,
and compile the Inno Setup installer.

The older manual repair and 237-pass result are evidence, **not a pass for
this newly modified builder or its Windows executable**. A successful build
must finish all these stages and produce the verified installer. Do not
distribute an old or partially built executable if a gate fails.
