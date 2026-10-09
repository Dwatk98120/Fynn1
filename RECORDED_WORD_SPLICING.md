# Recorded Word Splicing

First Sound Helper can now use locally stored student word recordings for corrected-sentence playback.

How it works:
1. A word recording is placed in the app-private `student_word_bank` directory.
2. The filename identifies the word, for example `cat_1712345678.wav`.
3. During suggested-sentence playback, the app looks for recordings of each sentence word.
4. If every word has a student recording, the app plays those recordings sequentially with short pauses.
5. If one or more words are missing, the app falls back to Android TTS rather than pretending the student's voice is available.

This approach does not create a synthetic voice model or upload voice data.

For child voice data, obtain caregiver/guardian consent and provide deletion controls.
