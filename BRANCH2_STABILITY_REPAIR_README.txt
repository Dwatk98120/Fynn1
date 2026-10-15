HEARLIUM PARENT PC - BRANCH 2 STABILITY REPAIR

Source: HEARLIUM_BRANCH2_PHONEME_LABEL_DECODER_FIXED_COMPLETE.zip
This is a source ZIP, not a precompiled Windows installer.

Changes:
- Parent PC GUI checks the running Hearlium health endpoint before launching another server.
- Frozen server launcher also skips duplicate startup when a compatible instance exists.
- Full Python analysis exceptions are written to %LOCALAPPDATA%\Hearlium\ParentPC\analysis_errors.log.
- HTTP 500 responses direct operators to that diagnostic file.
- Previous phoneme tokenizer decoder is retained; do not claim its model accuracy is validated.
- Recordings and learning folders are not removed or reset.

Important: A previous log showed a 500 response without traceback. This package adds diagnostic logging, but the actual decoder/model exception cannot be confirmed until the next test.

Build the Windows installer using the included BUILD_HEARLIUM_INSTALLER.bat, following README_BUILD_THIS_INSTALLER.txt.
Upload files ONLY to hearlium-parent-pc-integration. Do not change main.

Test:
1. Close all Hearlium windows and reopen the installed app after rebuilding.
2. Click Start Parent PC twice: second click must reuse the server.
3. Record speech, click Analyze, inspect results.
4. If analysis fails, send analysis_errors.log from %LOCALAPPDATA%\Hearlium\ParentPC.
