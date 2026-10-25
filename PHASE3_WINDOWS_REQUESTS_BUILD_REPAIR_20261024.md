# Hearlium Branch 2 — Windows Requests Build Reliability Hotfix

## Confirmed Windows test failure

The first Silero VAD installer build stopped at pytest collection with three
`ModuleNotFoundError: No module named 'requests'` errors. David checked
`.installer_venv\Scripts\python.exe -m pip show requests` and confirmed the
dependency was absent from that specific environment. Installing the official
`requests==2.32.3` there allowed the identical suite to complete with
**234 passed, 3 skipped, zero failures** (October 24, 2026).

The root reason that the earlier scripted install did not leave requests
available has not been established. Do not mislabel the original failure as a
Silero model error or assert that manual installation permanently fixed it.

## What changed

- Immediately before regression tests, the Windows builder checks that the
  actual isolated Python executable can import `requests`.
- If missing, it installs the pinned `requests==2.32.3` wheel into that same
  interpreter, checks the import again, and stops on any failed repair.
- The full pytest regression suite runs with that explicit Python executable.
- An additional lightweight regression test checks the build script safeguards.
- No other installer stages, Inno Setup release version, Android files, audio,
  observation logic, caregiver decisions, learning history or Main branch
  have been changed. Silero VAD 6.2.3 and its offline packaging remain in place.

## Building

1. Extract this **complete source ZIP** into a new folder, or apply to the
   working Branch 2 source (not Main). Do not install over a trusted baseline
   until the resulting Windows installer has passed validation.
2. Run `BUILD_HEARLIUM_INSTALLER.bat` as usual. It recreates the isolated
   `.installer_venv` automatically: there is no need to manually preinstall
   `requests` on the user's global Python.
3. Confirm the new `Checking requests in the isolated installer/test
   environment...` line, followed by 234 or more passed regression tests and
   any explicitly justified skips. A new test increases the possible count.
4. Let the builder continue through `verify_silero_vad.py`, offline model
   checks, PyInstaller and Inno Setup. **A passing regression suite alone is
   not proof that the Windows EXE or installer has successfully been built.**
5. After installation, reanalyze a protected recording and confirm
   `sileroVAD.status` is `evaluated` and the original SHA-256 is unchanged.

This ZIP contains full source and Windows installer build instructions, not a
precompiled installer. If the repair fails, capture the build log and stop;
do not use a potentially stale executable from an earlier installation.
