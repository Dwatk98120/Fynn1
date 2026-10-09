# Parent PC Local Backend — Phase 1

This phase removes legacy cloud backend from the normal Android analysis path.

## Architecture

Android phone -> local Wi-Fi/LAN -> Parent PC API -> 13-layer analysis/learning -> Android result

The Android app remains the main user-facing app. The Parent PC only takes over the heavier backend work.

## First run on Windows

1. Extract the project to the Parent PC.
2. Double-click `parent_pc_local/setup_and_start.bat`.
3. The first run installs the Python dependencies and may take a while because the speech model stack is large.
4. When the server starts, the window prints an address such as:
   `http://192.168.1.25:8000`
5. On the Android app tap **Parent PC Connection**.
6. Enter the address shown by the PC and tap **Test Parent PC**.
7. Save the address.
8. Record speech and tap **Analyze speech**.

The Android phone and Parent PC must be on the same local network.

## Windows Firewall

Windows may ask whether Python can communicate on private networks. Allow it on **Private networks** so the Android phone can reach port 8000.

## Data

The existing server learning store remains local to the Parent PC. `data/` and `server/data/` remain ignored by Git.

## Phase 1 limitation

This is a development launcher and still requires Python on the PC. A later phase will bundle the server and models into a normal Windows installer so parents do not need to install Python manually.
