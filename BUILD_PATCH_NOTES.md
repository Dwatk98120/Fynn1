# Hearlium Complete Rebuild - Build Patch

Fixes legacy distance pip flags, requires and verifies Bluetooth helper, uses explicit dotnet publish output, logs errors to hearlium_build.log, and verifies frozen executable before Inno Setup.

Extract all files and run BUILD_HEARLIUM_INSTALLER.bat. If it fails, send hearlium_build.log.

Static checks only; Windows compilation not yet tested.
