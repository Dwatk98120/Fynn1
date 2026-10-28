$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$project = (Get-Location).Path
$env:LOCALAPPDATA = Join-Path $project 'reports/tk_repair_frozen_appdata'
$python = Join-Path $project '.installer_venv/Scripts/python.exe'
$exe = Join-Path $project 'dist/HearliumParentPC/HearliumParentPC.exe'
& $python installer/verify_tk_build.py
if ($LASTEXITCODE -ne 0) { throw 'Build interpreter Tk failed' }
& $python installer/verify_0417_archive.py
if ($LASTEXITCODE -ne 0) { throw 'Reanalysis archive guards failed' }
& $python installer/verify_frozen_gui.py
if ($LASTEXITCODE -ne 0) { throw 'Frozen GUI failed' }
foreach ($mode in @('self-test', 'verify-layer2', 'verify-android-retry')) {
    $process = Start-Process -FilePath $exe -ArgumentList "--$mode" -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput "reports/tk_repair_$mode.out.txt" -RedirectStandardError "reports/tk_repair_$mode.err.txt"
    if ($process.ExitCode -ne 0) { throw "Frozen $mode failed: $($process.ExitCode)" }
    Write-Output "Frozen $mode passed"
}
& $python installer/verify_layer2_build.py stamp
if ($LASTEXITCODE -ne 0) { throw 'Build stamp failed' }
& $python installer/verify_layer2_build.py verify
if ($LASTEXITCODE -ne 0) { throw 'Build verification failed' }
function Get-BundleSnapshot {
    $bundle = Join-Path $project 'dist/HearliumParentPC'
    $snapshot = [ordered]@{}
    Get-ChildItem -LiteralPath $bundle -Recurse -File | Sort-Object FullName | ForEach-Object {
        $snapshot[$_.FullName.Substring($bundle.Length + 1)] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
    }
    return $snapshot
}
$before = Get-BundleSnapshot
$before | ConvertTo-Json -Depth 4 | Set-Content 'reports/tk_repair_packaged_files.json'
$shortDrive = $null
foreach ($letter in @('H', 'Q', 'R', 'S', 'T', 'W', 'X', 'Y', 'Z')) {
    if (-not (Test-Path "${letter}:\")) {
        & subst "${letter}:" $project
        if ($LASTEXITCODE -eq 0) { $shortDrive = "${letter}:"; break }
    }
}
if (-not $shortDrive) { throw 'No short drive available' }
try {
    & 'C:/Program Files (x86)/Inno Setup 6/ISCC.exe' '/FHearliumSetup-0.4.17-TkRepair' "$shortDrive\installer\Hearlium.iss"
    if ($LASTEXITCODE -ne 0) { throw 'Installer compilation failed' }
} finally {
    & subst $shortDrive /D
}
$after = Get-BundleSnapshot
if (($before | ConvertTo-Json -Compress) -cne ($after | ConvertTo-Json -Compress)) {
    throw 'Distribution changed while packaging'
}
$setup = Get-Item 'installer/output/HearliumSetup-0.4.17-TkRepair.exe'
$hash = (Get-FileHash -LiteralPath $setup.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
"$hash  $($setup.Name)" | Set-Content 'installer/output/HearliumSetup-0.4.17-TkRepair.exe.sha256'
[ordered]@{
    installer = $setup.FullName; sha256 = $hash; bytes = $setup.Length
    executableSha256 = $before['HearliumParentPC.exe']
    frozenGui = 'passed'; frozenSelfTest = 'passed'; frozenLayer2 = 'passed'
    frozenAndroidRetry = 'passed'; legacyReanalysisArchiveGuards = 'passed'
    bundleUnchangedDuringCompilation = $true
    bundleManifest = 'reports/tk_repair_packaged_files.json'
    installed = $false
} | ConvertTo-Json | Set-Content 'installer/output/BUILD_0.4.17_TK_REPAIR_VALIDATION.json'
Write-Output "Verified installer: $($setup.FullName) SHA256 $hash"
