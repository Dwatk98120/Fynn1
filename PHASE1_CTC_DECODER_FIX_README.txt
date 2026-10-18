HEARLIUM - Phase 1 CTC tokenizer decoding repair

Base: Hearlium_Branch2_Speech_Recognition_Phase1_REPAIR.zip

Fix: Both the main decoder and the segmenter now map CTC IDs using the model processor tokenizer vocabulary, not model.config.id2label (which may contain LABEL_0 placeholders). Blank token uses tokenizer.pad_token_id. Unknown token IDs and placeholder tokenizer vocab raise explicit errors rather than fabricating speech. Per-run confidence remains aligned with decoded tokens.

No changes to Android or caregiver approval.

Build: replace your source with this ZIP contents and rebuild/reinstall the Windows Parent PC server executable using your existing installer build workflow. Updating the ZIP alone does not update an already installed server.

Test: visit http://127.0.0.1:8000/health, then analyze a fresh counting 1-12 recording. Do not approve incorrect output for learning.

Checks: Python AST and source regression tests. Actual model inference and Windows installer execution have NOT been validated in this environment.
