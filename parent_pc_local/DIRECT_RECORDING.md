# Parent PC Direct Recording Mode

This adds a standalone one-on-one recording station to the Parent PC.

## Features
- Record directly from the Windows microphone
- 16 kHz mono WAV capture compatible with `/v1/analyze-audio`
- Start / Stop controls
- visible recording state and timer
- local saved recording files
- speaker/student ID
- optional context
- Analyze Recording button
- analysis through the same Parent PC 13-layer backend
- basic top-candidate/observed-phoneme result view
- local recording folder access

## Start it
After `setup_and_start.bat` has created the Python 3.12 environment:

`parent_pc_local\start_direct_recording.bat`

For the full Parent PC station:

`parent_pc_local\start_parent_pc_full_station.bat`

The full-station launcher starts the local API, the Bluetooth helper when already compiled, and the Direct Recording window.

## Current scope
This phase creates the direct recording workflow and sends recordings through the same analysis endpoint used by Android. Caregiver approval, richer recording history, and dedicated Parent PC learning-center integration can be expanded in a later phase.
