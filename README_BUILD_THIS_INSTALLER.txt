HEARLIUM CURRENT BUILD: 0.4.21 | ANDROID 3.3.4/CODE10
Read BUILD_0.4.21_README.txt, TEST_RESULTS_0.4.21.md and GITHUB_0.4.21_UPLOAD.md.
Complete offline NLTK resources and safe Android audio cleanup are included.
Earlier builder/handoff notes below are historical. No automatic installation.

HEARLIUM BRANCH 2 - CURRENT SOURCE HANDOFF 0.4.20

Read BUILD_0.4.20_README.txt and TEST_RESULTS_0.4.20.md first.
Includes the earlier Tk/phoneme/capture/legacy-alias repairs and now rejects
conflicting modern receipt identities/sources and same-ID declared sources.
Use BUILD_HEARLIUM_INSTALLER.bat with Python 3.12 x64, Tcl/Tk, .NET 8 SDK and
Inno Setup 6. Do not install tkinter through pip. PocketSphinx is pinned to 5.0.4.
The fresh builder output is installer/output/HearliumSetup.exe (version 0.4.20).
The separately prepared artifact is installer/output/HearliumSetup-0.4.20.exe.
The GitHub-ready ZIP contains source only; see GITHUB_0.4.20_UPLOAD.md.
Source regression: 493 passed, 3 optional private-adult-audio tests skipped.
Refer to the current release proof for frozen/installer validation.
Installed-device acceptance remains pending. No automatic installation.
Preserve original recordings, metadata, approvals, duplicate history and audits.

Historical cumulative builder notes follow and may name superseded fixes.

HEARLIUM BRANCH 2 - WORD-ASR / SILERO CROSSCHECK AND SPEECH-WINDOW QUALITY HOTFIX (25 OCT 2026)

WHAT THIS NEWEST CUMULATIVE BUILD ADDS:
- wordAsrActivityReview compares the time intervals of independent
  Faster-Whisper SEGMENTS with Silero candidate voice activity. A trailing
  segment outside Silero, such as the extra unverified "You" on the 50% adult
  test, is flagged for caregiver listening without changing the transcript.
- speechWindowQualityReview measures original WAV amplitude within Silero
  candidate intervals. It shows when the whole-session mostly-silent label
  may be affected by long deliberate pauses, while explicitly PRESERVING the
  original global recordingQuality label and all its warnings.
- recognizerDisagreementReview summarizes conflicts among word ASR, phoneme
  observations and Silero. Agreement is not accuracy; Silero is not a
  child-speaker classifier or noise removal.
- Parent PC dashboard/Evidence clearly show the new warnings and window
  measurements. No new automatic learning or approval path was introduced.

NEXT TEST: Build and install only after all Windows dependency tests, frozen
server/executable checks and Inno build pass. Reanalyze your existing
UNAPPROVED 50%, 70%, 80% and noisy 80% adult WAVs. In the 50% recording,
confirm the extra Faster-Whisper "You" is now flagged in
wordAsrActivityReview without being deleted. Confirm the long pause is
distinguished in speechWindowQualityReview and the original WAV SHA-256,
quality screen, word transcript and prior caregiver approvals are unchanged.
See PHASE3_SPEECH_CROSSCHECK_QUALITY_HOTFIX_20261025.md for details.

PREVIOUS CUMULATIVE BUILD: BACKGROUND / PHONEME INTEGRITY HOTFIX (25 OCT 2026)

THIS BUILD ADDS:
- Review-only Silero vs phoneme-candidate disagreement. Phoneme fragments
  outside detected voice activity are kept under unverifiedCandidates, not
  deleted or displayed as ordinary word suggestions. No voice/source is
  automatically labeled as the child; with no Silero activity detections the
  system does not blanket-hide the recording's word suggestions.
- Word-ASR digits 0-99 are normalized to English for model-to-model phoneme
  agreement. Unhandled numerals are explicitly marked for caregiver review.
- The long word-ASR span boundary warning now catches the tested ~20-second
  eight-word segment, without trimming or rewriting any evidence.
- A separate provisional utteranceProsodyReview removes the long pauses
  between Silero candidate utterances from estimated local rate. It does not
  modify the existing whole-session prosody finding or imply speaker ID.
- Parent PC recording review reports held phoneme candidate counts and the
  provisional within-utterance rate when available.

Build from BUILD_HEARLIUM_INSTALLER.bat as described below. Review the NEW
analysis JSON fields speechActivityCandidateReview and
utteranceProsodyReview. See PHASE3_BACKGROUND_PHONEME_INTEGRITY_HOTFIX_20261025.md
for tested values and limitations. The earlier cumulative notes follow.

PREVIOUS BUILD: LAYER 2 BACKGROUND SINGING REVIEW HOTFIX (24 OCT 2026)

Complete cumulative Parent PC Windows installer SOURCE project.
No Android app, Android workflow, or Main branch changes.

NEW IN THIS CUMULATIVE HOTFIX:
- Analysis JSON now includes speakerSourceReview. A background singer, other
  person and the intended student are NOT automatically distinguishable.
  Late phonemes are never proof that the student kept speaking.
- phonemeTimingReview.postWordToDuringWordPeakRmsRatio compares sound-energy
  windows AFTER the unverified word-ASR end with windows during the word-ASR
  hypothesis. This corrects a misleading fixed-3-second comparison when the
  target phrase lasts longer than 3 seconds. It is NOT a VAD or speaker ID.
- Parent PC Record & Analyze includes "Background audio (caregiver label)".
  For an adult recording with a distant song containing vocals, select
  "Music with singing" and click "Save Sound Label". The label and its audit
  history are saved ONLY in the recording's sidecar JSON, never inside the
  immutable raw acoustic observation, model output, or personalized learning.
  Loading a recording from History restores its saved label.
- Evidence / AI Dashboard warn about unverified target-speaker attribution.
  The full raw CTC output, WAV checksum, existing reviews and Android code
  remain untouched. The tests benchmarked the supplied adult WAV without
  shipping the private audio or JSON inside the installer source.

NEXT TEST AFTER INSTALL: use a short *adult* test phrase with music/singing
playing farther from the Parent PC. Confirm the target words, inspect
speakerSourceReview and phonemeTimingReview, save the caregiver background
label, reopen the recording from History, and check that WAV and prior review
are unchanged. If you have only the old sound JSON, reanalyze that WAV to
generate these NEW interpretation-only fields; older exports remain intact.

Full details: PHASE3_LAYER2_BACKGROUND_VOCAL_ATTRIBUTION_HOTFIX_20261024.md

1. Preserve your last working installer and local data.
2. Extract this ZIP into a NEW folder, preferably a short path (C:\H23).
3. Close Hearlium Parent PC and its API/server before installing.
4. Double-click BUILD_HEARLIUM_INSTALLER.bat in the newly extracted folder.
   Do NOT start with COMPILE_INSTALLER_ONLY.bat: that script reuses an EXE.
5. Wait for dependencies, all regression tests, BOTH frozen EXE checks,
   verified build stamp, and Inno Setup compilation to finish successfully.
6. Install the NEW installer\output\HearliumSetup.exe.
7. Start Hearlium and wait until the AI models are ready. For this hotfix,
   use an unapproved ADULT TEST recording made directly on the Parent PC.
   Select it from Recording History and click Analyze Recording. Export its
   NEW analysis JSON. Never reanalyze an approved learning reference solely
   for this test; retain prior history and original audio.

   In analysisResult.recordingStorage verify:
   saved = true
   sha256 = SHA-256 digest of the unchanged WAV
   source = parent_pc (NOT android)

   A newly submitted Android recording, or a saved Android recording
   reanalyzed from the PC History screen, must have source = android.
   Existing old exports are intentionally NOT rewritten or relabeled.

   On Record & Analyze, look for "PHONEME TIMING WARNING" displayed ahead
   of the large raw phoneme sequence when recognizers disagree. The review
   shows only a RAW PREVIEW; the complete unchanged raw phoneme transcript
   remains in Evidence and Raw JSON. Technical recording quality is NOT
   recognition accuracy or verified noise/speaker isolation.
8. In analysisResult.observation.rawEvidence.acoustic verify:
   activityEvidenceVersion = layer2-activity-tail-v2
   activityEstimateIsVerifiedSpeech = false

   If two separated sound islands are both plausible activity, status is
   ambiguous_separated_activity_islands and both endpoint/quiet are null.
   Do not interpret a null as proof the recording contains no speech.

9. In analysisResult.speechActivityReview verify:
   reviewVersion = layer2-speech-ambient-crosscheck-v1
   wordAsrEndSeconds = unverified Faster-Whisper candidate endpoint or null
   phonemeCandidateEndSeconds = unverified CTC candidate endpoint or null
   endDisagreementSeconds = difference when both are available
   candidateSpeechEndSeconds = null when recognizers disagree substantially

   This is a review-only interpretation: no sound is automatically certified
   speech or ambient noise, and no caregiver learning changes are made.

10. In analysisResult.phonemeTimingReview verify:
    reviewVersion = layer23-boundary-phoneme-reliability-v1
    status = unverified boundary review, depending on the recording
    extendedWordSegmentNeedsReview = true/false warning on a long ASR span
    uncorroboratedLateSegmentCount = late CTC segments beyond word hypothesis
    automaticWordSuggestionHoldCount = how many late segments were withheld
    loudestSoundWindowStartSeconds = non-speech-specific energy measurement
    lateToEarlyPeakWindowRmsRatio = sound-energy comparison, not speech proof

    Some segmentCandidates may now have status
    uncorroborated_late_phoneme_review and no ranked word candidates.
    This hold requires substantial recognizer disagreement and a non-stretched
    word timestamp. If ASR timing is itself suspicious, no CTC guess is hidden
    based solely on that timestamp. Complete raw CTC phonemes and WAVs remain
    untouched and available for caregiver review.

11. Parent PC API copies saved by the server are now named parent_pc_api_*
    and carry source = parent_pc. These are separate from the original local
    microphone WAV. Older android_* mislabeled copies are not changed or
    deleted. Parent PC recording history and Android upload compatibility are
    retained; duplicate server-side history copies are still a known limitation.

The supplied adult test WAVs were verified by matching their saved SHA-256
hashes, but the WAV files are NOT distributed in this ZIP. See
PHASE3_LAYER23_BOUNDARY_PHONEME_RELIABILITY_HOTFIX_20261024.md for details.

COMPILE_INSTALLER_ONLY.bat rejects absent or outdated verified build stamps
and any change to the tested EXE or tracked sources. It is safe ONLY as a
short-path Inno Setup retry after the FULL builder has completed on this source.

This is an installer BUILD PROJECT, not a precompiled Windows EXE.
This release makes false late phoneme *suggestions* less likely, but does not
claim accurate speech/ambient classification or calibrated phoneme accuracy.
The entire 13-layer analysis stack still needs real-world accuracy validation.
No Windows installer compilation or Windows run was performed in this Linux
verification environment; see PHASE3_PARENT_PC_SOURCE_AND_PHONEME_REVIEW_HOTFIX_20261024.md.
October 25, 2026: This cumulative Branch 2 source includes the Recording
History titles and search hotfix. Once installed, open Recording History;
existing recordings receive suggested display titles from verified saved
metadata/analysis. Use "Save Suggested Titles for Existing" to persist those
titles, or select any recording and enter a personal Title, comma-separated
Tags and Notes, then click "Save Label". "Use Suggested Title" clears only
the custom title. Original WAVs, protected observation JSON, and learning
records are never edited by label operations. See
PHASE3_RECORDING_TITLE_TAG_SEARCH_HOTFIX_20261025.md for test instructions.

RECORDING HISTORY SEARCH/SORT REPAIR — 2026-10-25b (Inno 0.4.7)
This cumulative Branch 2 package adds a visible Search button next to the
Recording History search field. Press Search (or Enter) after typing; the
number of matched recordings and current sort mode will be displayed.
For sorting, select an order and click Apply Sort, OR click a column heading;
click the same heading again to reverse that order. The footer must say
"Search/Sort repair 2026-10-25b" after installing this exact build.
If the marker is absent, a previous Windows build is still running. Close
old Hearlium processes and install the newly built 0.4.7 installer.
See PHASE3_RECORDING_HISTORY_SEARCH_SORT_REPAIR_20261025.md for tests.
