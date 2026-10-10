$ErrorActionPreference = "SilentlyContinue"
Write-Host ""
Write-Host "===================================================================="
Write-Host " First Sound Helper - Parent PC Bluetooth Check"
Write-Host "===================================================================="
$devices = Get-PnpDevice -Class Bluetooth | Where-Object { $_.Status -eq "OK" }
if (-not $devices) {
    Write-Host "No active Windows Bluetooth devices were detected."
    Write-Host "Check that Bluetooth is installed, enabled, and has a working driver."
    exit 1
}
Write-Host "Bluetooth hardware/services detected:"
$devices | Select-Object Status, FriendlyName | Format-Table -AutoSize
Write-Host ""
Write-Host "Stage 1 setup: pair this PC from Android Bluetooth settings, then"
Write-Host "select the PC in First Sound Helper > Parent PC Connection > Bluetooth Setup."
Write-Host "Wi-Fi/LAN remains the data path for recordings and analysis."
Write-Host "===================================================================="
Write-Host ""
