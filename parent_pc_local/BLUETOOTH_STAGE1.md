# Bluetooth Parent PC Integration — Stage 1

This build adds the first safe Bluetooth integration stage without changing the existing LAN analysis path.

## Included
- Android Bluetooth/Nearby Devices permissions
- Bluetooth adapter availability check
- Android paired-device list
- Open Android Bluetooth settings for discovery/pairing
- Select and remember the trusted Parent PC Bluetooth device
- Parent PC Windows Bluetooth adapter check script
- Existing Wi-Fi/LAN Parent PC address and `/health` testing remain unchanged

## Data path
Bluetooth is currently used for pairing/identity setup. Audio and analysis requests continue over the local Wi-Fi/LAN API. This avoids sending large audio payloads over Bluetooth and preserves the current stable Parent PC API.

## Next stages
1. Exchange Parent PC IP/API port through a Bluetooth handshake service.
2. Automatic reconnect and readiness status.
3. Fallback messaging when Bluetooth is paired but LAN is unavailable.
