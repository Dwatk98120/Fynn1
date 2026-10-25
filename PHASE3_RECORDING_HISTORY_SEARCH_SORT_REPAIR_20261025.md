# Hearlium Branch 2 — Recording History Search and Sort Repair

Date: October 25, 2026 | Windows Inno Setup version: **0.4.7**

This is a cumulative source hotfix built on the October 25 Recording Titles
and Tags hotfix. Windows installer must still be compiled and exercised on
the target Parent PC; this ZIP is source, not a precompiled installer.

## User-reported problems addressed

1. **Search field accepted typing with no visible Search action.** A bold
   **Search** button now appears immediately after the field. The Return key
   triggers the same action. The Search action reloads newly saved titles and
   metadata before filtering, then reports the match count or "No matches".
2. **Sorting seemed nonfunctional.** Add an explicit **Apply Sort** button
   beside the dropdown. The same operation is available from each clickable
   table heading, where a second click reverses the column order. All sorting
   choices appear in the dropdown, and a status line shows the active order.
3. **Date sorting used WAV modification time.** Newest/oldest now use the
   recording's saved creation timestamp. Reanalyzing, copying, and importing
   files do not reorder historical date results solely by file mtime.
4. **Parent PC word suggestions were absent from the searchable Word field.**
   Original unverified word recognition is now read from a matched *verified*
   saved result for both local Parent PC and Android recordings, without
   running analysis, approving suggestions, or changing protected evidence.

## How to confirm the correct build is installed

1. Build with `BUILD_HEARLIUM_INSTALLER.bat` from this new extracted folder;
   install `installer\output\HearliumSetup.exe` after closing old Hearlium
   processes. The Windows setup version is now **0.4.7**.
2. Open **Recording History**. Near the search/filter controls, confirm the
   visible text **Search/Sort repair 2026-10-25b**. If it isn't there,
   the new build is not the one currently running.
3. Enter `student-1` or a known filename in the Search box and click Search;
   verify the result count changes. Try a manually saved custom tag, too.
4. Click **Oldest first**, then **Apply Sort**; October 12 recordings should
   appear before more recent recordings. Click **Newest first**, then
   **Apply Sort** to reverse. Click the **Date** column heading twice and
   verify the order reverses as well.
5. Click other headings: **Student name**, **Recording Title / Tag**,
   **Speaker ID**, **Status**, **Word / suggestion**, **Recording**. The status
   line and row order should both update.
6. Search `hello` on any recording with a verified saved Parent PC ASR result;
   the suggestion is *not* an approved word or personalized learning input.
7. Confirm existing WAVs, original observation IDs, review history and
   learned examples remain untouched; do not approve uncertain test speech.

## Verification in this environment

* `server/tests/test_phase3_recording_history_search_sort_actions.py`: tests
  each sort direction, metadata-vs-mtime ordering, search matches, simulated
  visible Treeview reordering, column-header reversal, Enter/button actions,
  and Parent PC word suggestions.
* The existing title/tag storage tests and prior Silero/word-analysis tests
  are retained. The source and ZIP are additionally checked for syntax and
  archive integrity.
* Full Windows frozen EXE/UI acceptance tests remain required on David's PC.

**Protected baseline:** The original October 25 title-tag hotfix was not
changed. Only the copied Branch 2 source received this repair. The Android
working APK, Main branch and local 13-layer speech-analysis pipeline are
unchanged.
