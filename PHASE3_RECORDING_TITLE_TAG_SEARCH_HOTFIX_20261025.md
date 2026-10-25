# Hearlium Branch 2 — Recording History Titles & Tags

**October 25, 2026. Windows Parent PC; Inno Setup version 0.4.6.**

This is a cumulative source hotfix built on
`Hearlium_Branch2_Phase3_Speech_Crosscheck_Quality_Hotfix_20261025`.
It does **not** modify Main or the Android working baseline. This package is
builder source; compile the Windows installer with `BUILD_HEARLIUM_INSTALLER.bat`.

## What changed

* An additional **Recording Title / Tag** column is available in **Recording History**.
  For each existing saved WAV, the Parent PC displays a deterministic suggested
  title from caregiver-supplied notes/context, explicitly identified background
  labels, a caregiver-confirmed word when truly confirmed, or **unverified**
  recognition text from a **verified** saved analysis. If none is available,
  it falls back to recording source/time or filename. No audio is reanalyzed.
* The selected recording has editable **Title**, **Tags**, and **Notes** fields.
  Enter comma-separated tags and click **Save Label**. A manual title always
  overrides suggestions. **Use Suggested Title** clears the override without
  clearing tags and notes.
* **Save Suggested Titles for Existing** persists generated labels for older
  recordings without overwriting any custom title; rerunning this action is safe.
* Recording History **Search** now finds suggested/manual titles, tags and
  label notes in addition to name, ID, filename and recognized-word fields.
  **Recording title A–Z** is a new optional sorting mode.

## Protection and limitations

* Labels are held outside protected audio/evidence in
  `%LOCALAPPDATA%\Hearlium\ParentPC\recording_titles.json`, with an append-only
  `%LOCALAPPDATA%\Hearlium\ParentPC\recording_titles_audit.jsonl` change log.
  Atomic replacement and identity checks protect existing custom labels.
* Recording WAVs, original metadata, observation IDs, analysis exports,
  approved clips, reference recordings, and learning ledgers are not modified
  by these UI features.
* Suggestions are **labels**, not verified speech, diagnoses or learning
  approvals. "AI suggestion (unverified)" means exactly that. The system cannot
  infer recording mic gain (50%, 70%, 80%) from signal amplitude; enter that
  manually if it was not explicitly recorded.
* Labels are local to this Parent PC. The planned **future** child-specific
  export/import feature must include their metadata, but is not implemented here.
* No new ASR, acoustic layer, PDF printer, or Wav2Vec2 word recognizer was
  added in this labeling hotfix. Previously integrated Phase 3 hotfixes are
  carried forward. Other independently approved future backlog work remains
  queued and should not be represented as implemented.

## Windows smoke test

1. Extract this ZIP to a **new folder**. Run
   `BUILD_HEARLIUM_INSTALLER.bat` and install its generated Windows installer.
   Keep your established Parent PC installation data backed up.
2. Open **Recording History**. Confirm older recordings display a suggested
   title. Test a recording with notes, one with unverified analysis, and one
   without any saved analysis. Every AI-derived word should be labeled as
   **unverified**.
3. Select the 80% noisy adult test, enter custom Title
   `80% Mic – TV and music`, Tags `adult test, noisy, 80%`, and optional Notes.
   Click **Save Label**. Search `80%`, `noisy`, and the notes text.
4. Click **Save Suggested Titles for Existing**, verify it **does not overwrite**
   the manually entered title. Restart the app and confirm labels persist.
5. Click **Use Suggested Title** on the selected recording and confirm its
   manually saved tags remain while the title reverts to the generated label.
6. Play and reanalyze an original recording. Compare original SHA-256 and
   saved evidence with the pre-hotfix values. No approval or learning should
   be triggered by labeling. Run a single caregiver-approved fixture only
   through the existing protected workflow; do not approve uncertain test data.
7. Verify search and sorting with multiple students and near-identical WAV
   names, and verify recording still works while labels exist.

## Development verification

The new model-free tests are in
`server/tests/test_phase3_recording_title_tags_hotfix.py`. They cover
generated title wording, safe index persistence, custom override precedence,
audits, same-name identity safety, corrupted indices, interrupted atomic
writes, and title/tag/note search.

Full Windows installer compilation, UI operation and dependency-complete
regression tests must pass on the Windows builder before accepting this hotfix.
