# One-Tap Parent PC Pairing

This build adds a simpler user-facing connection flow on top of Bluetooth Stages 1–3.

## Parent PC
Run:

`parent_pc_local\pair_phone.bat`

The Pair Phone window:
- starts the local Parent PC API
- starts the compiled Bluetooth RFCOMM helper when available
- shows the current local IP for diagnostics only
- provides a large Pair Phone action
- opens Windows Bluetooth Settings when needed

## Android
Use:

**Parent PC Connection → Easy Connect**

The guided flow:
- shows a simple connection status
- offers Find Parent PC the first time
- remembers the selected Parent PC
- attempts Bluetooth handshake automatically after selection
- receives the PC's current IP/port
- verifies `/health` over Wi-Fi/LAN
- offers Connect Now and Check Connection on later uses

The user should not need to manually type an IP address or port during normal use.

## Existing transport design remains unchanged
- Bluetooth: discovery, pairing, endpoint exchange, reconnect coordination
- Wi-Fi/LAN: audio and analysis payloads
