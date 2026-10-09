# Live Speech privacy notes

Live Speech uses Android speech recognition for partial text and captures short 16 kHz mono audio chunks for optional phoneme analysis.

- Microphone permission is required.
- The prototype does not save live chunks to the app's recording history automatically.
- When phoneme analysis is enabled, short chunks are sent to the configured analysis API.
- Use HTTPS for any deployed API.
- Obtain caregiver/guardian consent before recording or transmitting a child's voice.
- For production, add authenticated API access, encryption in transit/at rest, retention limits, deletion controls, and an explicit no-training policy for child recordings unless separately authorized.
