param([string]$ApplicationRoot = 'C:\Program Files\Hearlium')
$ErrorActionPreference = 'Stop'
$workspaceRoot = Split-Path -Parent $PSScriptRoot
$resourceRoot = Join-Path $workspaceRoot 'models\nltk_data'
$releaseProof = Get-Content -LiteralPath (Join-Path $workspaceRoot 'SOURCE_RELEASE_0.4.20_VERIFICATION.json') -Raw | ConvertFrom-Json
$expectedExe = $releaseProof.installerVerification.executableSha256
$actualExe = (Get-FileHash -LiteralPath (Join-Path $ApplicationRoot 'HearliumParentPC.exe') -Algorithm SHA256).Hash
if ($actualExe -ne $expectedExe) { throw 'Installed executable does not match the verified 0.4.20 build; refusing repair.' }
$manifest = Get-Content -LiteralPath (Join-Path $resourceRoot 'resources_sha256.json') -Raw | ConvertFrom-Json
$resourceFiles = @('taggers/averaged_perceptron_tagger.zip', 'corpora/cmudict.zip',
    'corpora/cmudict/cmudict', 'corpora/cmudict/README',
    'taggers/averaged_perceptron_tagger_eng/averaged_perceptron_tagger_eng.weights.json',
    'taggers/averaged_perceptron_tagger_eng/averaged_perceptron_tagger_eng.tagdict.json',
    'taggers/averaged_perceptron_tagger_eng/averaged_perceptron_tagger_eng.classes.json')
$destinationRoot = Join-Path $ApplicationRoot '_internal\nltk_data'
foreach ($relative in $resourceFiles) {
    $fileName = Split-Path -Leaf $relative
    $expected = $manifest.filesSha256.$relative
    if (-not $expected -or (Get-FileHash -LiteralPath (Join-Path $resourceRoot $relative) -Algorithm SHA256).Hash -ne $expected) {
        throw "Staged resource integrity conflict: $fileName"
    }
    $destination = Join-Path $destinationRoot $relative
    if ((Test-Path -LiteralPath $destination) -and (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash -ne $expected) {
        throw "Existing installed resource conflicts; refusing overwrite: $fileName"
    }
}
if ((Test-Path -LiteralPath $destinationRoot) -and ((Get-Item -LiteralPath $destinationRoot).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    throw 'Resource destination must not be a link.'
}
[IO.Directory]::CreateDirectory($destinationRoot) | Out-Null
foreach ($relative in $resourceFiles) {
    $fileName = Split-Path -Leaf $relative
    $destination = Join-Path $destinationRoot $relative
    if (-not (Test-Path -LiteralPath $destination)) {
        $destinationParent = Split-Path -Parent $destination
        [IO.Directory]::CreateDirectory($destinationParent) | Out-Null
        $temporary = Join-Path $destinationParent ($fileName + '.' + [guid]::NewGuid().ToString('N') + '.tmp')
        try {
            $bytes = [IO.File]::ReadAllBytes((Join-Path $resourceRoot $relative))
            $stream = [IO.File]::Open($temporary, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
            try { $stream.Write($bytes, 0, $bytes.Length); $stream.Flush($true) } finally { $stream.Dispose() }
            [IO.File]::Move($temporary, $destination)
        } finally {
            if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary }
        }
    }
    if ((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash -ne $manifest.filesSha256.$relative) {
        throw "Installed resource failed SHA-256 verification: $fileName"
    }
}
Write-Output 'Verified complete offline NLTK corpus/tagger resources. No executable, recording, metadata, approval or audit history was overwritten.'
