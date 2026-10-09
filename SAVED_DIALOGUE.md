# Saved dialogue

The Android project now includes local storage helpers for dialogue history.

Each analyzed recording can be stored in the app's private storage with:
- `recording.wav`
- `analysis.json`

For production, expose caregiver-only history, export, and delete controls in the UI. Do not retain children's audio on the cloud by default; disclose retention and obtain appropriate caregiver consent.
