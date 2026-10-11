param(
  [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
$python = Join-Path $rootDir ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
  Write-Host "Parent PC virtual environment was not found."
  Write-Host "Run parent_pc_local\setup_and_start.bat first."
  exit 1
}

$payload = & $python "$scriptDir\bluetooth_handshake.py"
Write-Host ""
Write-Host "Hearlium Bluetooth Stage 2 handshake:"
Write-Host $payload
Write-Host ""
try {
  Set-Clipboard -Value $payload
  Write-Host "Handshake copied to clipboard."
} catch {
  Write-Host "Could not copy to clipboard; copy the text above manually."
}
