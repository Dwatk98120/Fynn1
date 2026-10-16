HEARLIUM BRANCH 2 — WORD BOUNDARY SUGGESTION REPAIR

Build source: previous Branch2 Segmentation Safety Repair ZIP.

Changes:
- Adds conservative proposedSegmentJoins to /v1/analyze-audio JSON.
- Examines adjacent CTC segments separated by at most 0.24 seconds, where at least
  one segment is short, and suggests a joined word only if candidate confidence
  >= 0.60 and improves over the unjoined candidates by at least 0.08.
- Avoids joining two segments that both already have plausible word candidates.
- Original transcript, wordSegments, raw evidence, and approved learning remain
  unchanged. A proposal is NOT confirmed speech and does NOT train the model.
- No counting-specific word order or hardcoded answer is introduced.

Limitations:
- This is a conservative repair, not a guarantee of recognizing 1–12.
- Does not change Android app or Windows UI; proposals appear in API output.
- It does not fix Windows backend startup / connection-refused errors.
- Rebuild the Windows installer using BUILD_HEARLIUM_INSTALLER.bat and your
  established build prerequisites. Do not use an older prebuilt installer.

Tests: python -m pytest -q server/tests/test_segment_repair.py
