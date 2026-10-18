# Hearlium enhanced decipher — dual engine

Adds optional independent word-level ASR to Parent PC, while preserving original phoneme model and observations. Android displays word transcription separately from raw phonemes. Neither is confirmed speech or a clinical conclusion.

## Parent PC installation

In the Parent PC Python environment, from the repository root:

    python -m pip install -r server/requirements-word-asr.txt

Restart the Parent PC server. First analysis downloads the `base.en` model (internet required). Optional `HEARLIUM_ASR_MODEL=small.en` uses a larger/slower model. `HEARLIUM_WORD_ASR=off` disables it. If unavailable, existing phoneme analysis still works.

## Test

Build APK with existing GitHub Actions workflow; update Parent PC from same ZIP. Record counting 1–12. Inspect WORD RECOGNITION separately from RAW SOUND OBSERVATION. Compare against original audio; never automatically treat expected words as observed or approve learning from ASR guesses.

## Limitations

This is an actual additional ASR path, but improved accuracy is not established without testing. It does not add word-level forced alignment, validated consonant omission detection, or automated accuracy scoring.
