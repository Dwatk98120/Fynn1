# Personal Word Bank

The app now includes a **Personal Word Bank** screen.

Caregivers can:
- enter a word
- record the student saying it
- play the recording
- delete the recording

The recordings are stored locally under the app-private `student_word_bank` directory.

Suggested sentence playback first tries to use the student's recorded words. If required words are missing, the app falls back to Android TTS.

No synthetic voice model is created by this feature.
