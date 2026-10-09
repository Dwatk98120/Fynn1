# Parent PC Only Architecture

First Sound Helper / Hearlium uses the Parent PC as its only analysis backend and does not use a cloud analysis service.

## Current analysis path

Android phone -> local network -> Parent PC -> speech analysis / learning -> Android result

## Required behavior

- Android must never fall back to a cloud backend.
- If the Parent PC is not configured or unavailable, the app must show a clear Parent PC connection message.
- Recordings and approved learning data remain local unless the user explicitly exports them.
- Bluetooth may be added for discovery, pairing, status, and automatic local-network setup.
- Wi-Fi/LAN remains the preferred transport for larger audio and analysis payloads.

## Connection requirements

The Parent PC local API provides:
- `/health`
- `/v1/analyze-audio`
- `/v1/learning/feedback`

The Android app uses the saved Parent PC address for all analysis and feedback operations.
