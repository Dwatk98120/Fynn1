HEARLIUM BRANCH 2 - PHONEME DECODER HTTP 503 COMPATIBILITY REPAIR

Source: HEARLIUM_BRANCH2_HTTP503_DIAGNOSTIC_REPAIR(1).zip
Scope: Parent PC phoneme decoder and error presentation only. Android files untouched.
No GitHub branch was modified. Use hearlium-parent-pc-integration, NOT main.

CAUSE FROM THE USER'S DIAGNOSTIC LOG:
Tokenizer vocabulary size: 47; model CTC output classes: 45.
A tokenizer can contain added tokens that are not model output classes. The old
code rejected the entire tokenizer when ANY ID exceeded the model's output range.

REPAIR:
- Check every output ID 0..44 has a corresponding tokenizer token.
- Allow extra tokenizer IDs outside the model's output range without decoding them.
- Preserve CTC blank, repeated-token collapsing, delimiter, and confidence logic.
- Reject missing/ambiguous/placeholder output symbols and invalid CTC blank IDs.
- Display API error detail in the Parent PC recording dialog when analysis fails.
- Include regression tests for 47 tokenizer entries / 45 model output classes.

BUILD:
1. Back up the existing installation and recordings/learning data.
2. Extract this ZIP into a NEW folder (do not mix with older source files).
3. Follow the included Windows build instructions and installer scripts.
4. Close the old Parent PC application and stop the old API process before
   launching the newly built application; the launcher can reuse a running API.
5. Record or select a WAV and click Analyze Recording.
6. If an error persists, report the full new popup detail and the file
   %LOCALAPPDATA%\Hearlium\ParentPC\analysis_errors.log

VALIDATION:
- Python syntax compilation: passed.
- Five local synthetic decoder unit tests: passed.
- Windows installer/APK/real Hugging Face model and end-to-end speech analysis:
  NOT tested in this environment. This is a source ZIP, not a built .exe.

This repair does not alter, migrate, or delete stored recordings or profiles.
