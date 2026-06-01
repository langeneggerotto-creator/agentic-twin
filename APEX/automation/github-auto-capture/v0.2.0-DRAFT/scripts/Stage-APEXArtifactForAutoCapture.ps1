[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ArtifactPath,
    [string]$ControlCenterRoot = 'C:\Users\lange\Dropbox\Online Businesses\APEX Systems\Documentation\Learning System\CONTROL_CENTER',
    [string]$ArtifactId = 'APEX-AUTO-STAGED-ARTIFACT',
    [string]$TruthStatus = 'CREATED_ARTIFACT_NOT_OUTCOME_PROOF'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if (-not (Test-Path -LiteralPath $ArtifactPath)) { throw "Artifact not found: $ArtifactPath" }

$InboxRoot = Join-Path $ControlCenterRoot 'auto_capture_inbox'
New-Item -ItemType Directory -LiteralPath $InboxRoot -Force | Out-Null
$BatchId = 'BATCH-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff')
$BatchRoot = Join-Path $InboxRoot $BatchId
New-Item -ItemType Directory -LiteralPath $BatchRoot -Force | Out-Null

$Item = Get-Item -LiteralPath $ArtifactPath
if ($Item.PSIsContainer) {
    Copy-Item -LiteralPath $Item.FullName -Destination $BatchRoot -Recurse -Force
} else {
    Copy-Item -LiteralPath $Item.FullName -Destination $BatchRoot -Force
}

$Receipt = [ordered]@{
    batch_id = $BatchId
    artifact_id = $ArtifactId
    staged_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    source_name = $Item.Name
    truth_status = $TruthStatus
    status = 'STAGED_FOR_AUTOMATIC_PREFLIGHT_AND_CAPTURE'
    boundary = 'Submission remains subject to governed branch preflight and validation.'
}
$Receipt | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $BatchRoot 'stage_receipt.json') -Encoding UTF8
Write-Host ("STAGED: {0}" -f $BatchRoot) -ForegroundColor Green
Write-Host 'The scheduled APEX capture sweep will preflight and submit eligible contents automatically.' -ForegroundColor Cyan
