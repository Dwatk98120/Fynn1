# Hearlium Reference Audio Matching — initial implementation

This build adds a local WAV library for numbers one through twelve, with **standard** and **student-specific** recordings. The Parent PC window now includes **Reference Audio Library**. Start the Parent PC server, open the library, enter the speaker ID, choose the library type and number, and upload WAV recordings. Choose an isolated student WAV clip, play it alongside a selected reference, and request exploratory comparison suggestions.

## Included
- Multiple WAV reference recordings per number and per student, stored outside the installed application under `%LOCALAPPDATA%\Hearlium\ParentPC\reference_audio` (or `HEARLIUM_REFERENCE_DIR`).
- WAV validation, mono/16-kHz standardization, reference listing, playback and upload.
- Simple log-spectrum dynamic-time-warping comparison, ranked by *relative acoustic distance*, not recognition probability.
- Comparison suggestions are explicitly `reviewRequired: true`, `learningEligible: false` and do not modify any of the 13 existing analysis layers or student learning profiles.
- New FastAPI routes: `POST /v1/reference-audio`, `GET /v1/reference-audio`, `GET /v1/reference-audio/{kind}/{number}/{reference_id}`, `POST /v1/reference-audio/compare`.
- Parent PC window for uploading and comparing clips with two separate playback buttons.
- Installer batch now stops if .NET 8 SDK / Bluetooth compilation / Bluetooth EXE copying fails.

## Limitations / follow-on work
- Comparisons are for **isolated number clips**. They do not automatically find all twelve numbers in a continuous counting WAV or identify individual consonant errors.
- A low acoustic distance does **not** establish the spoken number, phoneme identity, omission, or clinical accuracy. Different voices and microphones affect scores. Listen and confirm manually.
- This is a **first integration**, not a validated speech recognition improvement. Automatic boundary-guided alignment, phoneme-by-phoneme reference alignment, and a saved human-confirmation UI are not implemented yet.
- The existing API exposes endpoints on the configured LAN; do not expose port 8000 to the public internet. Treat children's recordings as sensitive and secure the computer.
- Windows installer and Android APK cannot be compiled/tested in this environment. Build using `BUILD_HEARLIUM_INSTALLER.bat` on Windows with .NET 8 SDK and Inno Setup.
