# Bluetooth Stage 2 — automatic Parent PC connection handshake

Stage 2 now includes an actual Bluetooth RFCOMM handshake path.

## Android
After Stage 1 pairing and choosing the trusted Parent PC:
1. Tap **Connect to Parent PC**.
2. Android opens an RFCOMM connection to the paired Windows computer.
3. The Parent PC sends a compact JSON payload containing its current LAN IP and API port.
4. Android saves that endpoint.
5. Android immediately tests `http://<host>:<port>/health`.
6. Large audio and analysis traffic stays on Wi-Fi/LAN.

The fixed service UUID is:

`7b8d3f52-9f24-4c87-a4e1-3d11f5d8a701`

## Windows Parent PC
Source for the RFCOMM service is in:

`parent_pc_local/bluetooth_service/`

Run:

`parent_pc_local/build_bluetooth_service.bat`

to compile the self-contained Windows helper. This requires the .NET 8 SDK on the development PC. Once built, the published helper can be included in the final Hearlium Windows installer so end users will not need the SDK.

For diagnostics, `show_bluetooth_handshake.bat` still prints the same JSON payload, and the Android Bluetooth screen includes a manual **Handshake Test** fallback.

## Connection fallback
If Bluetooth succeeds but `/health` cannot be reached, Android reports that Bluetooth is working but Wi-Fi/LAN is unavailable or cannot reach the Parent PC.

Stage 3 will focus on automatic reconnect, background status, and recovery behavior.
