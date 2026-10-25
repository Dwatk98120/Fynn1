# Hearlium Branch 2 — Layer 2/3 Boundary and Phoneme Reliability Hotfix

October 24, 2026. Complete cumulative Parent PC source package, with Android
unchanged and Main frozen.

## Why this change was needed

David confirmed two adult reference recordings with one brief phrase, followed
by ambient sound. The exported results were **not reliable speech endpoints**:

| Confirmed phrase | Original WAV SHA-256 | Duration | Word-ASR end | Full-recording CTC end |
|---|---|---:|---:|---:|
| Test one two three | `f0305fc39204d5fb4d99cb282c4e153e0dc177f26e5c8bb718ab64c897eedcc5` | 12.818s | 2.11s | 12.678s |
| Thank you | `e3f97feec7b3a8d88c4f8ec8b71f96872e72ce455ec51d9127c8daae9d7e1fe8` | 12.220s | 8.67s | 12.02s |

The independent word recognizer got the phrases right. The CTC phoneme engine
continued beyond the spoken phrase, and the **Thank you** word segment also
ran abnormally long. A late, louder energy burst in that file showed why an
energy threshold alone cannot prove speech. The precise real-world speech
endpoints are not established by these audio-energy checks.

## Fixes

1. `server/phoneme_timing_review.py` adds independent, interpretation-only
   timing diagnostics: unusually extended word hypothesis, CTC timestamps
   beyond word hypotheses, loudest half-second sound window, and late/early
   energy comparison. This is **not a validated VAD**, cannot establish a
   spoken consonant, and does not identify ambient sound as fact.
2. Analysis results contain `phonemeTimingReview`, with version
   `layer23-boundary-phoneme-reliability-v1`, clear uncertainty, human-review
   requirements, and explicit prohibition on automatic learning.
3. CTC segments *wholly after* an unverified word-ASR segment end plus 0.30s
   are flagged as late but remain present in `wordSegments` and the immutable
   observed transcript. Only when both recognizers differ by over 0.8s **and**
   the word segment is not unusually stretched are those late segments withheld
   from automatic dictionary matching. They then receive
   `uncorroborated_late_phoneme_review`. If the word hypothesis itself may be
   stretched (as in the **Thank you** test), no phoneme candidate is hidden
   based on that weak timestamp. CTC-only mode with no word hypothesis remains
   available: absence of word-ASR is not proof of silence.
4. Adjacent candidate merges are prevented from reintroducing word guesses
   for those uncorroborated late segments. Human review and correction remain
   available. Other segment candidates and the 13 existing layers remain.
5. Parent PC Evidence view explains the new review with visible warnings.
6. Windows frozen EXE self-test and installer integrity stamp require the
   new version. PyInstaller includes both module import paths explicitly.

## Regression tests

- 207 automated server/Parent PC tests passed with both original adult WAVs
  supplied externally for SHA-256/energy tests.
- Test metadata supports a **read-only optional** WAV check without placing
  user recordings in the distributed installer. Use:

  ```bat
  set HEARLIUM_LAYER23_REFERENCES=C:\path\to\test_wavs
  py -3.12 -m pytest -q server\tests
  ```

- Expected filenames in that folder:
  `test_20261024_132827_719783_516c7010.wav` and
  `android_test_20261024_182430_927833_test_20261024_132409_647652_f4f76685.wav`.
- For routine builds without those WAVs, the optional real-recording check is
  skipped. All synthetic safety checks still execute.
- Tests cover no ASR, very slow real speech, stretched ASR text, late CTC,
  synthetic loud ambient bursts, unchanged evidence, UI wiring and build guard.

## Limits and safeguards

Word and CTC timestamp warnings are conservative heuristics; their status is
not a clinical accuracy score and should not be used to erase genuine
unrecognized speech. The original WAVs and existing analysis history were not
modified. There is no training from these examples without caregiver approval.

Only the Parent PC source was changed. No Android or GitHub workflow edits.
The full Windows PyInstaller/Inno build and end-to-end recording verification
must be performed on David's Windows system. No Windows EXE was built here.
