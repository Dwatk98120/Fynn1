# Hearlium Branch 2 — Layer 2 Background Singing and Speaker-Source Review

October 24, 2026 — cumulative Windows Parent PC installer **source**, not an EXE.

## Why this hotfix exists

An adult spoke "Test 1, 2, 3" near the Parent PC microphone; music with
**singing** continued in the background. Faster-Whisper hypothesized the target
phrase ending at 4.85 s, but phoneme-CTC emitted segments until 30.26 s.
Those late tokens may correspond to the singer, other sound, or model error;
the current engines cannot establish speaker identity or a verified speech end.

The existing timing safeguard correctly withheld 46 late phoneme **word
suggestions**. It did not delete the original raw observations. The old
"late-to-early" energy ratio used a fixed 3-second split and therefore
included some of the target's 3–5-second phrase in its "late" window. This
build keeps that legacy field for compatibility but adds an explicitly
**unverified ASR-relative** sound-energy comparison. The adult recording gave
legacy ratio 0.871 versus new post-word ratio 0.0748. Neither measures speech
accuracy, singer identity or confirmed background noise.

## Changes

- New JSON `analysisResult.speakerSourceReview`, a **review-only** explanation
  of possible background vocal sources and unverified speaker attribution.
  It NEVER says the model confirmed singing or isolated the target speaker.
- `analysisResult.phonemeTimingReview.postWordToDuringWordPeakRmsRatio` plus
  interpretation/validity flags and the older unchanged 3-second diagnostic.
- Parent PC review screen lets a caregiver independently label background
  audio as music with/without singing, distant conversation, ambient noise,
  mixed/unsure, or unspecified. The "Save Sound Label" action versions the
  human label in the local WAV's `.json` metadata with an audit trail. It
  does not alter the WAV, the original acoustic evidence or model outputs,
  and does not train any speaker model. History restores the saved label.
- Parent PC Evidence and Dashboard explain that sung vocals are non-target
  candidates until a human validates their source and that even a future VAD
  cannot identify the intended speaker solely from voice activity.
- Incremented frozen-source build guard. `COMPILE_INSTALLER_ONLY.bat` cannot
  package an EXE built with the prior review code unless a new full build
  and frozen self-test have been completed.

## What this does NOT do

- It does **not** install Silero VAD or Wav2Vec2. Those remain backlog
  priorities, after their respective baseline validation.
- It does **not** perform automatic music detection, speaker identification,
  source separation, word-alignment verification or model retraining.
- It does **not** classify every late phoneme as noise or suppress genuine
  late target speech. Existing uncertainty guards still apply.
- It does **not** change the Android source, Android workflows or Main branch.

## Verified locally

- 227 Parent PC/server regression tests passed (2 optional/other tests skipped).
- Adult WAV checksum `52bd1456a29cab9ac0e786b48cd57e5ab16af3fecf726328de258f39d4af8f93`
  matched its saved analysis JSON before and after the new interpretation.
- The actual WAV and its private analysis JSON are **not** included in this
  ZIP. No real child recordings or approval histories are included.
- Test inputs cover late sung/speech-like sound, misleading 3-second energy
  splits, versioned human notes, missing models, and immutable WAV evidence.
- Actual frozen Windows EXE/installer assembly and interactive Windows UI
  installation remain to be verified on the user's Windows build machine.

## Windows installation and acceptance test

1. Preserve the previous known-good installer and data. Extract this ZIP to a
   fresh short directory such as `C:\H24`.
2. Run **`BUILD_HEARLIUM_INSTALLER.bat`**, not the Inno-only retry first.
   Let tests, model bundling, frozen self-check and Inno Setup finish.
3. Install the newly built `installer\output\HearliumSetup.exe`; open Parent
   PC and wait for its local API to say Running.
4. Record an adult phrase with a distant song that includes singing. Confirm
   that Faster-Whisper's text is a **candidate** and that late CTC output
   is not silently turned into approved student words.
5. In the Record & Analyze tab, set `Background audio (caregiver label)` to
   `Music with singing`, then click `Save Sound Label`.
6. Inspect Evidence and Raw JSON. Look for `speakerSourceReview` status,
   `targetSpeakerIdentityVerified: false`, and
   `postWordRatioIsSpeechOrSpeakerEvidence: false`.
7. Reopen the same recording from History. Confirm the label remains present,
   the previous feedback/review still exists, and the original WAV hash is
   unchanged. Reanalysis creates a new versioned interpretation without
   modifying the original WAV or prior analysis export.

All speech analysis, storage and learning remain on the Windows Parent PC.
Main stays frozen; this is a separate Branch 2 source package.
