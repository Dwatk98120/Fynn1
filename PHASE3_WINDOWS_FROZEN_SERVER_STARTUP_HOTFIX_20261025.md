# Hearlium Phase 3 — Windows Frozen Server Startup Repair (2026-10-25)

## Failure reproduced from Windows screenshot

The installed `HearliumParentPC.exe --server` raised:

`ModuleNotFoundError: No module named 'websockets.legacy'`

The previous frozen `--self-test` imported Uvicorn without loading its selected
protocol modules; PyInstaller can omit optional imports loaded by Uvicorn at
server startup even if `import uvicorn` succeeds.

## Scoped repair

- Uvicorn is configured with `ws="none"`, `http="h11"`, `loop="asyncio"`.
  Hearlium's local Parent PC/Android API currently uses HTTP, not WebSockets.
  The BootstrapServer explicitly closes unexpected WebSocket scopes.
- The PyInstaller spec collects `h11`, the HTTP parser chosen at runtime.
- The **same configuration** is used by the server and `--self-test`, which now
  runs `uvicorn.Config.load()` inside the finished frozen Windows executable
  before Inno Setup can create an installer. The specific missing-optional-
  import failure should now abort the build, not surprise the installed user.
- Four regression tests protect the protocol configuration and frozen build
  gate. If WebSocket routes are added in a later release, revisit this setting
  and explicitly package/test a supported WebSocket implementation.

## What has not changed

- Windows Inno version 0.4.6, all 13 speech-analysis layers and Silero VAD.
- Android app, local recordings, protected observations, caregiver approvals,
  evidence checksums or learning history.
- Main remains frozen; changes belong to Branch 2 only.

## Windows validation required

1. Extract this full source ZIP to a NEW directory.
2. Run `BUILD_HEARLIUM_INSTALLER.bat` from that directory.
3. Confirm all package audits, regression tests, model checks, frozen self-test
   and Inno Setup compilation pass.
4. Install on a test Parent PC with existing records preserved; start the
   Parent PC API and verify `/health` responds on port 8000 without crashes.
5. Verify direct PC recording, a saved analysis and Android local HTTP upload.

This package was reviewed/tested as source on Linux. A completed Windows
installer/actual server start cannot be claimed until Windows verification.
