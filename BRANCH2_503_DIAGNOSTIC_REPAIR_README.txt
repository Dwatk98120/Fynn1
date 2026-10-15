HEARLIUM BRANCH 2 - TARGETED HTTP 503 DIAGNOSTIC REPAIR

What was found:
The existing /v1/analyze-audio endpoint explicitly returns HTTP 503 when
PhonemeVocabularyError is raised. The previous analysis_errors.log logger only
handles unexpected exceptions, so it never recorded this error.

What changed:
The PhonemeVocabularyError handler now writes the exact cause, model name,
output dimensions, and tokenizer/model vocabulary sizes to:
%LOCALAPPDATA%\Hearlium\ParentPC\analysis_errors.log

This is a DIAGNOSTIC repair, not a claim that the model/decoder compatibility
has been fixed. It intentionally does not invent phonemes or silently substitute
a different speech model.

Instructions:
Build/install using the existing Parent PC build instructions.
Record or select an existing recording, click Analyze Recording, and upload
analysis_errors.log if 503 remains.

No existing recordings or learning data should be deleted.
Use ONLY hearlium-parent-pc-integration (Branch 2); Main remains untouched.
