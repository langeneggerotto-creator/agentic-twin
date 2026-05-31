[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$SourcePath,
    [int]$MaxFileSizeMB = 5
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if (-not (Test-Path -LiteralPath $SourcePath)) { throw "Preflight source does not exist: $SourcePath" }

$BlockedExtensions = @('.env','.pem','.key','.pfx','.p12','.sqlite','.db','.kdbx')
$BlockedNameFragments = @('credential','private-key','password','local-secret')
$SensitiveMarkers = @('BEGIN PRIVATE KEY','BEGIN RSA PRIVATE KEY','Authorization: Bearer','client_secret','private_key')
$Failures = @()
$Held = @()

foreach ($File in (Get-ChildItem -LiteralPath $SourcePath -File -Recurse)) {
    $Relative = $File.FullName.Substring($SourcePath.Length).TrimStart('\','/')
    $Ext = $File.Extension.ToLowerInvariant()
    $LowerName = $File.Name.ToLowerInvariant()
    if ($BlockedExtensions -contains $Ext) {
        $Failures += "Blocked extension: $Relative"
        continue
    }
    foreach ($Fragment in $BlockedNameFragments) {
        if ($LowerName.Contains($Fragment)) { $Failures += "Blocked sensitive filename: $Relative" }
    }
    if ($File.Length -gt ($MaxFileSizeMB * 1MB)) {
        $Held += "Held for large-file/media path: $Relative"
        continue
    }
    if (@('.md','.json','.jsonl','.yaml','.yml','.csv','.txt','.html','.py','.ps1','.toml') -contains $Ext) {
        $Text = Get-Content -LiteralPath $File.FullName -Raw -ErrorAction SilentlyContinue
        if ($null -ne $Text) {
            foreach ($Marker in $SensitiveMarkers) {
                if ($Text.Contains($Marker)) { $Failures += "Sensitive marker found: $Relative" }
            }
        }
    }
}

if ($Held.Count -gt 0) { $Held | ForEach-Object { Write-Host $_ -ForegroundColor Yellow } }
if ($Failures.Count -gt 0) {
    $Failures | ForEach-Object { Write-Error $_ }
    throw 'ARX automatic-capture preflight failed. No automatic submission is permitted for this payload.'
}
Write-Host 'ARX automatic-capture preflight passed for the supplied payload.' -ForegroundColor Green
