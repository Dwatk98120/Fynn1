# Bluetooth helper .NET SDK build repair

The Bluetooth helper targets net8.0-windows10.0.19041.0, but its Microsoft.Windows.SDK.Contracts package was 10.0.26100.1742. The newer Windows SDK contracts platform version can exceed the project TargetPlatformVersion and trigger NETSDK1135.

Changed only parent_pc_local/bluetooth_service/HearliumBluetoothService.csproj: Microsoft.Windows.SDK.Contracts 10.0.26100.1742 -> 10.0.19041.38. This keeps the Windows 10 19041 target and avoids changing the runtime paths used by the installer and launcher.

Run BUILD_HEARLIUM_INSTALLER.bat on Windows with .NET 8 SDK installed. Confirm Bluetooth helper publish succeeds before proceeding. This ZIP has not been Windows-built in this environment.
