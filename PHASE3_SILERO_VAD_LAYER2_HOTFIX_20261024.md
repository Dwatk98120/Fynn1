# Hearlium Branch 2 — Layer 2 Silero VAD Hotfix (October 24, 2026)

## What changed

1. Integrated the official **Silero VAD 6.2.3** as a third, independent
   speech-activity view beside energy analysis, Faster-Whisper and the
   original phoneme recognizer.
2. Added `sileroVAD` to each Parent PC / Android analysis result:
   inference status, package version, candidate speech intervals, totals,
   timing and human-review safeguards. Full phoneme observations remain
   unchanged. Layer 2 also compares its final candidate boundary with the
   unverified word-ASR endpoint.
3. The Parent PC Dashboard and Evidence screen now show Silero's status,
   speech intervals, and a clear disclaimer that TV dialogue and singing can
   trigger VAD. Silero **does not** identify the target student.
4. Added a review warning for *localized clipping* hidden by low overall
   clipping percentages on longer recordings. Original WAV is never altered.
5. The Windows build installs official Silero VAD 6.2.3, validates **actual
   local model inference** before freezing, collects the model/reader in
   PyInstaller, and includes the upstream MIT license notice in the installer.
6. Bumped the Windows Inno Setup application version to **0.4.6**.
7. Added independent unit/regression tests; the existing Android app and its
   source code are unchanged.

## Build and install

Upload the **complete source ZIP** to the working Branch 2 repository or
extract it into a new folder. On a Windows BUILD machine, run
`BUILD_HEARLIUM_INSTALLER.bat` from the project root. The script downloads
and verifies official Python packages and the previously required offline
ASR/phoneme models. It now also installs and smoke-tests Silero VAD before
building a Windows Inno Setup installer. Installed Parent PCs do not need a
network connection for Silero model inference.

The downloadable ZIP contains build **source and configuration**, NOT an
already-compiled Windows executable. Do not distribute a build if its
dependency checks, real Silero inference check or full test suite fails.

## Verification with David's adult reference recordings

The first protected baseline to review is the October 24 ~30.76-second
Parent PC WAV with two counting phrases, background TV dialogue and localized
clipping around 21–23 seconds. This test WAV is intentionally **not included**
in the distributable source ZIP.

After installing on the Windows Parent PC:

1. Reanalyze that recording. Confirm that `sileroVAD.status` is
   `evaluated` (not merely `not_run` or `unavailable`), with plausible
   individual `speechSegments` and `modelPackageVersion`.
2. Inspect **AI Dashboard** and **Evidence** tabs for VAD intervals and
   explicit `targetSpeakerIdentityVerified: false` behavior.
3. Compare Silero timestamps, word-ASR timings, old energy activity and the
   actual played-back recording. Mark discrepancies for caregiver review.
4. Capture a 20-second TV-only recording and a quiet-room recording; verify
   that VAD cannot approve TV words for the child or silently alter acoustic
   observations, even when the detector correctly notices a voice.
5. Repeat short phrases close to the mic with a distant conversation, music
   with singing, quiet gaps, low-volume child speech and variable distance.
   Check misses, false positives, timing and speaker-attribution warnings.
6. Confirm the Layer 1 **localized clipping** warning for saturated intervals.
7. Analyze the same original twice: SHA-256 stays identical, previous
   analysis history stays intact, and no unconfirmed learning occurs.

## Boundaries and limitations

- **VAD means voice activity detection**, not speaker identification. It
  can identify distant speech or singing from TV as speech activity.
- VAD results are independent *interpretations*. They are never used to
  rewrite original audio, silently erase phoneme evidence, declare consonant
  omissions or authorize learning.
- On any model failure, `sileroVAD.status: unavailable` and an error code
  are returned; the existing processing path remains available. The Windows
  **build** nevertheless refuses to package an unverified Silero model.
- Unit tests mock heavy inference and run without Torch. The Windows builder
  additionally requires a real inference smoke test; the user should verify
  recordings on the target Parent PC before approving Layer 2.
- No Wav2Vec2 word recognizer or multi-phone queue is added in this release.
  Those remain separately prioritized. Main is frozen; Branch 2 only.

## Third-party notices

Silero VAD 6.2.3 and its package-bundled model are covered by the upstream
MIT license, reproduced in `THIRD_PARTY_NOTICES_SILERO_VAD.md`. Other
third-party speech models and libraries still require independent license
compliance review before distribution.
