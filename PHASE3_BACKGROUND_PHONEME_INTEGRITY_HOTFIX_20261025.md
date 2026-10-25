# Hearlium Branch 2 — Background / Phoneme Integrity Hotfix

Date: October 25, 2026. Complete **source** ZIP for the Windows Parent PC
installer workflow. Branch 2 only; **Main is frozen**. No Android code or
installer-version changes. All analysis, storage and learning remain local to
the Windows Parent PC.

## Purpose and changes

1. **Independent Silero activity review.** `speechActivityCandidateReview`
   records which CTC-derived phoneme segment indices lie outside detected
   candidate speech activity. Affected ranked words move from `candidates`
   to `unverifiedCandidates` in a derived interpretation view; nothing is
   deleted from the original phoneme evidence, WAV, or analysis history.
   Silence/quiet atypical speech can be missed by Silero; a recording with
   **zero** detected speech intervals retains normal word suggestions for
   caregiver review. Silero cannot distinguish a child from TV singing.
2. **Number-normalized recognizer comparison.** Digits 0–99 in the ASR
   hypothesis are converted to spoken English before phoneme comparison.
   Unsupported integers yield an explicit unresolved status, not a partial
   agreement score. This is agreement between models, not measured accuracy.
3. **Overlong word timing warning.** A candidate word span exceeding
   1.8 seconds per hypothesized word (or five seconds) is flagged for review;
   no word, timestamp, or audio content is clipped or silently corrected.
4. **Separate within-utterance prosody estimate.** `utteranceProsodyReview`
   excludes long intentional pauses *between* Silero activity islands, while
   preserving the historical whole-session `prosody` observation. Both
   estimates may include another speaker and are not clinical assessments.
5. **Parent PC display.** Recording results indicate background phoneme
   segments withheld from ordinary suggestions and a provisional local
   speaking-rate band, if one can be estimated.

## Observed comparison on supplied unapproved adult tests

The test recordings are **not distributed** in this ZIP.

| Same 80% mic gain | Quieter background | Louder TV/music background |
| --- | ---: | ---: |
| Saved duration | ~26.7 s | ~25.7 s |
| Original CTC phoneme segments | 9 | 56 |
| Segments outside Silero activity, held for review | 0 | 44 |
| Whole-session rate (syllable peaks/s) | 0.375 | 0.351 |
| Provisional within-utterance rate (syllable peaks/s) | 2.326 | 2.093 |

These values are observations from the supplied adult test setup, **not**
validated improvements in child speech accuracy. The recognizer's complete
raw transcript, timestamps, checksum, audio and caregiver decision history
remain protected. These review flags must never create automatic learning.

## Testing and installation

- New model-free regression cases cover digit counting, unsupported numbers,
  overlong timing, protected candidates, missing/zero Silero activity, and
  long pauses in prosody. Relevant legacy phoneme/recognizer regressions
  were also run under Linux. A full Windows dependency/model/frozen-EXE
  installer build **has not been run in this environment**.
- Preserve your last working installer and original recordings; extract
  this source ZIP into a **new short directory**, e.g. `C:\H25`.
- Close the running Parent PC app/server. Execute
  `BUILD_HEARLIUM_INSTALLER.bat`, not `COMPILE_INSTALLER_ONLY.bat`, and
  require its full test, model, frozen-EXE and Inno checks to pass.
- Install the newly generated `installer\output\HearliumSetup.exe` only
  after the build reports success. Keep an older known-good installer ready.
- With an **unapproved adult recording** containing a known phrase, silence
  and background TV/music, compare the full JSON's original `wordSegments`
  with `segmentCandidates`, `speechActivityCandidateReview`,
  `utteranceProsodyReview`, `recognizerAgreement` and `phonemeTimingReview`.
  Inspect every uncertain word manually; verify previous approved child
  examples and reference files are unchanged.

## Explicit limitations

- Voice-activity detection is **not** noise removal, speaker separation,
  proof of silence, confirmed child speech or proof of any particular word.
- The legacy whole-session `prosody.speechRateBand` still includes long
  pauses; the new review view is separate and provisional.
- Model disagreement scores can remain low in music/noise, even when
  Faster-Whisper produced the intended phrase.
- Neither bundled Windows EXE nor Android APK was compiled here. The ZIP
  supplies Windows and Android project source; Android was not modified.
- Learning remains strictly tied to explicit caregiver-approved examples,
  with no automatic approval or training from these review views.
