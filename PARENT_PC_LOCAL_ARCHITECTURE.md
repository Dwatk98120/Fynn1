# Parent PC Local Architecture

Primary direction:

Android = recording, communication UI, playback, candidate selection, caregiver confirmation.

Parent PC = local API, 13-layer analysis, persistent observations, interpretations, approved learning, speaker profiles and future larger AI models.

legacy cloud backend is no longer required for the normal analysis path in this phase.

Connection flow:

Android -> `http://<parent-pc-lan-ip>:8000` -> `/v1/analyze-audio`
Android -> Parent PC -> `/v1/learning/feedback`
Android -> Parent PC -> `/health` for connection testing

Future phases should add automatic discovery/pairing, authentication, Windows background service startup, packaged installer, encrypted local transport where practical, and database-backed storage.
