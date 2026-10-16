HEARLIUM BRANCH 2 - ADAPTIVE WORD BOUNDARY REPAIR

What changed:
- Adaptive short-gap detection and fragment-aware word join proposals.
- Both proposedSegmentJoins (legacy) and mergedSegmentCandidates (new) returned.
- No original CTC wordSegments or observations are modified.
- Proposed joins are marked reviewRequired=true, learningEligible=false.
- Unconfirmed joins do not alter analysis confidence or omission flags.
- Python import fallback works for both package and direct server launches.

Validation performed:
- Four mocked-ranker tests passed, including replay of the 16 segment timestamps
  from student-1_20261016_130755; expected four join opportunities.
- Python source compiled successfully.

LIMITS:
- This is NOT an end-to-end phoneme-model test; the real candidate ranker may
  return different scores or words. Actual proposals require live retesting.
- Review proposals are exposed in analysis JSON. A clickable approval screen
  in the Parent PC GUI is NOT included in this repair; no auto-approval occurs.
- Existing API learning pathways have not been changed by this patch.

Install:
1. Back up your current working GitHub Branch 2.
2. Replace Branch 2 source with this ZIP's contents (not just the server folder).
3. Commit and push, then run BUILD_HEARLIUM_INSTALLER.bat on Windows.
4. Install the new build and record counting 1-12 again.
5. Export and send the raw *_analysis.json file for verification.

Look for:
  proposedSegmentJoins
  mergedSegmentCandidates
  segmentInterpretation.proposedMergeCount

Do not interpret a proposal as a verified correct word.
