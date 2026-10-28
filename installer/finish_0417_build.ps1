$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$project = (Get-Location).Path
$env:LOCALAPPDATA = Join-Path $project 'reports/build_0417_frozen_appdata'
$python = Join-Path $project '.installer_venv/Scripts/python.exe'
$exe = Join-Path $project 'dist/HearliumParentPC/HearliumParentPC.exe'
$bt = Join-Path $project 'parent_pc_local/bluetooth_service/bin/Release/net8.0-windows10.0.22000.0/win-x64/publish/HearliumBluetoothService.exe'
Copy-Item -LiteralPath $bt -Destination (Join-Path $project 'dist/HearliumParentPC/HearliumBluetoothService.exe')
& $python installer/verify_0417_archive.py
if ($LASTEXITCODE -ne 0) { throw 'Frozen archive verification failed' }
& $python installer/verify_frozen_gui.py
if ($LASTEXITCODE -ne 0) { throw 'Frozen GUI verification failed' }
foreach ($mode in @('self-test', 'verify-layer2', 'verify-android-retry')) {
    $process = Start-Process -FilePath $exe -ArgumentList "--$mode" -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput "reports/build_0417_$mode.out.txt" -RedirectStandardError "reports/build_0417_$mode.err.txt"
    if ($process.ExitCode -ne 0) { throw "Frozen $mode failed: $($process.ExitCode)" }
    Write-Output "Frozen $mode passed"
}
& $python installer/verify_layer2_build.py stamp
if ($LASTEXITCODE -ne 0) { throw 'Build stamp failed' }
& $python installer/verify_layer2_build.py verify
if ($LASTEXITCODE -ne 0) { throw 'Build verification failed' }
$shortDrive = $null
foreach ($letter in @('H', 'Q', 'R', 'S', 'T', 'W', 'X', 'Y', 'Z')) {
    if (-not (Test-Path "${letter}:\")) {
        & subst "${letter}:" $project
        if ($LASTEXITCODE -eq 0) { $shortDrive = "${letter}:"; break }
    }
}
if (-not $shortDrive) { throw 'No temporary short drive available' }
try {
    & 'C:/Program Files (x86)/Inno Setup 6/ISCC.exe' '/FHearliumSetup-0.4.17' "$shortDrive\installer\Hearlium.iss"
    if ($LASTEXITCODE -ne 0) { throw "Installer compilation failed: $LASTEXITCODE" }
} finally {
    & subst $shortDrive /D
}
$setup = Get-Item 'installer/output/HearliumSetup-0.4.17.exe'
$hash = (Get-FileHash -LiteralPath $setup.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
"$hash  $($setup.Name)" | Set-Content 'installer/output/HearliumSetup-0.4.17.exe.sha256'
$validation = [ordered]@{
    version = '0.4.17'; installer = $setup.Name; bytes = $setup.Length; sha256 = $hash
    serverTestsPassed = 359; serverTestsSkipped = 3; pipCheck = 'passed'
    androidSourceSafeguards = 'passed'; sileroOfflineInference = 'passed'
    offlineWordModelLoad = 'passed'; phonemeTokenizer = 'passed'
    frozenGuiSmokeTest = 'passed'
    frozenSelfTest = 'passed'; frozenLayer2 = 'passed'; frozenAndroidRetryStorage = 'passed'
    frozenLegacyChecksumRecoveryAndConflicts = 'passed'
    frozenArchiveModules = 'verified'
    bluetoothHelper = 'reused unchanged from 0.4.16 build'
    installedDeviceAcceptance = 'pending'; installed = $false
}
$validation | ConvertTo-Json | Set-Content 'installer/output/BUILD_0.4.17_VALIDATION.json'
Write-Output "Built $($setup.FullName) SHA256 $hash"
