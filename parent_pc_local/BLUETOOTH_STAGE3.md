# Bluetooth Stage 3 — automatic reconnect and status recovery

Stage 3 adds automatic connection maintenance on Android.

## Android behavior
- Keeps the last trusted Parent PC endpoint.
- Checks the Parent PC `/health` endpoint every 15 seconds while the app is active.
- Shows a saved connection state: connected, reconnecting, or not configured.
- After repeated LAN failures, attempts a lightweight Bluetooth RFCOMM handshake again.
- If Bluetooth returns a new IP/port, Android saves it and immediately retries the LAN health check.
- Prevents overlapping Bluetooth reconnect attempts.
- Stops the reconnect loop when the app leaves the foreground and restarts it on resume.

## Parent PC
`start_parent_pc_with_bluetooth.bat` starts:
1. the local Parent PC API, and
2. the compiled Bluetooth RFCOMM helper when available.

This completes the planned Stage 3 foundation. Future hardening can add Windows service startup, richer status UI, and backoff policies.
