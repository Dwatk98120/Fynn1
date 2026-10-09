# Live Speech mode

This build adds a **Live Speech** mode.

### What it does
1. Uses Android `SpeechRecognizer` partial results to show speech text with low latency.
2. Captures short audio windows at 16 kHz mono.
3. Periodically sends a short WAV chunk to the existing `/v1/analyze-audio` endpoint.
4. Shows a possible missing initial sound and candidate word only when the phoneme endpoint returns a candidate.
5. Stops all live capture when the user taps Stop or the dialog is dismissed.

### Important limitation
Live results are assistive/probabilistic. Partial speech recognition text is not treated as proof of an initial-consonant omission. The current phoneme model and candidate matching are starter-level and not clinically validated.

### API URL
The app continues to use the Gradle `FIRST_SOUND_HELPER_API_URL` configuration when available, with the Android emulator fallback `http://10.0.2.2:8787`.

### Production privacy
Use HTTPS, authenticated access, short retention, deletion controls, and caregiver/guardian consent for any child voice data sent to a server.
