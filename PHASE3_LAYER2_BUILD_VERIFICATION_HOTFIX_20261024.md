# Hearlium Branch 2 — Layer 2 Build Verification Hotfix (24 October 2026)

## Why this package exists

A fresh personal recording lasting 13.156 seconds contained roughly 80% quiet
audio and produced valid Layer 1 quality evidence, but its saved analysis lacked
all Layer 2 activity-tail fields. The recording was real and preserved; the
running Parent PC build could not be confirmed as the newest Layer 2 version.

The existing `COMPILE_INSTALLER_ONLY.bat` is designed to reuse an existing
`dist/HearliumParentPC` executable, and could therefore silently package a
previous build. A stale executable is a likely explanation, not a proven cause.

## Included fixes

1. Keep all cumulative Layer 1 and Layer 2 analysis, GUI, and server changes.
2. Run a synthetic Layer 2 activity/silence test **inside the frozen EXE**
   (`--verify-layer2`) before any Inno Setup packaging. The main frozen
   self-test also verifies the Layer 2 fields.
3. Stamp the just-tested EXE and critical source files with SHA-256 digests.
   The stamp contains program file hashes only, never student data or audio.
4. `COMPILE_INSTALLER_ONLY.bat` rejects an absent or mismatched stamp and
   instructs the operator to run the full builder. Inno Setup retry remains
   possible when the EXE and source are exactly the version verified.
5. Add regression tests for missing, changed, and unverified build stamps.
6. Update installer-build documentation with an explicit verification step.

## Install and validate

Use the **full** `BUILD_HEARLIUM_INSTALLER.bat` from a fresh extraction. Wait
for both frozen-EXE checks and the `Layer 2 build integrity verified` message.
Install the newly produced `installer/output/HearliumSetup.exe` and restart
Hearlium. Reanalyze the saved test recording and export the **new** Raw JSON.

Expected version marker at
`analysisResult.observation.rawEvidence.acoustic.activityEvidenceVersion`:
`layer2-activity-tail-v1`. `trailingQuietSeconds` should be substantial after
the speech. The activity endpoint is a heuristic energy boundary, **not**
validated speech recognition, phoneme alignment, or a clinical finding.

No Android app changes. Main branch remains protected; all services local to
the Windows Parent PC.

## Verification limits

Regression tests and source checks are performed in the Linux test workspace.
The actual PyInstaller/Inno Setup Windows build and installed EXE are tested
by the full build on the user's Windows PC. Layer 2 is not marked passed until
the installed version marker and real-recording evidence are reviewed.
