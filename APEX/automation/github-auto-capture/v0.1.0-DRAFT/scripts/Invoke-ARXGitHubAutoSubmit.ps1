[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$SourcePath,
    [string]$SessionId = ('ARX-' + (Get-Date -Format 'yyyyMMdd-HHmmss')),
    [string]$ControlCenterRoot = 'C:\Users\lange\Dropbox\Online Businesses\APEX Systems\Documentation\Learning System\CONTROL_CENTER',
    [string]$CaptureBranch = 'arx-autonomous-capture',
    [int]$MaxFileSizeMB = 5
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$RepoRoot = Join-Path $ControlCenterRoot 'github\agentic-twin'
if (-not (Test-Path (Join-Path $RepoRoot '.git'))) { throw 'Repository clone missing. Run Setup-ARXGitHubAutoCapture.ps1 once first.' }
if (-not (Test-Path -LiteralPath $SourcePath)) { throw 'Capture source does not exist.' }

$Allowed = @('.md','.json','.jsonl','.yaml','.yml','.csv','.txt','.html','.py','.ps1','.toml')
$Blocked = @('.env','.pem','.key','.pfx','.p12','.sqlite','.db','.kdbx')
$BlockedNames = @('credentials','private-key','password-file','local-secrets')
$SensitiveMarkers = @('BEGIN PRIVATE KEY','BEGIN RSA PRIVATE KEY','ACCESS_TOKEN=','API_KEY=','PASSWORD=','CLIENT_SECRET=','AUTHORIZATION: BEARER')

& git -C $RepoRoot fetch origin --prune
& git -C $RepoRoot checkout $CaptureBranch
& git -C $RepoRoot pull --ff-only origin $CaptureBranch

$Target = Join-Path $RepoRoot ('APEX\runtime-captures\' + $SessionId)
New-Item -ItemType Directory -Path $Target -Force | Out-Null
$Approved = @(); $Held = @(); $Rejected = @()

foreach ($File in (Get-ChildItem -LiteralPath $SourcePath -File -Recurse)) {
    $Relative = $File.FullName.Substring($SourcePath.Length).TrimStart('\','/')
    $Ext = $File.Extension.ToLowerInvariant()
    $NameLower = $File.Name.ToLowerInvariant()
    $NameBlocked = $false
    foreach ($BlockedName in $BlockedNames) { if ($NameLower.Contains($BlockedName)) { $NameBlocked = $true } }
    if (($Blocked -contains $Ext) -or $NameBlocked) {
        $Rejected += [pscustomobject]@{ file=$Relative; reason='PROHIBITED_AUTOMATIC_CAPTURE' }
        continue
    }
    if ((-not ($Allowed -contains $Ext)) -or ($File.Length -gt ($MaxFileSizeMB * 1MB))) {
        $Held += [pscustomobject]@{ file=$Relative; reason='HELD_FOR_GOVERNED_MEDIA_OR_LARGE_FILE_PIPELINE' }
        continue
    }
    $Text = (Get-Content -LiteralPath $File.FullName -Raw -ErrorAction Stop).ToUpperInvariant()
    $ContentBlocked = $false
    foreach ($Marker in $SensitiveMarkers) { if ($Text.Contains($Marker)) { $ContentBlocked = $true } }
    if ($ContentBlocked) {
        $Rejected += [pscustomobject]@{ file=$Relative; reason='SENSITIVE_CONTENT_MARKER_FOUND' }
        continue
    }
    $Destination = Join-Path $Target $Relative
    New-Item -ItemType Directory -Path (Split-Path $Destination -Parent) -Force | Out-Null
    Copy-Item -LiteralPath $File.FullName -Destination $Destination -Force
    $Hash = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash.ToLowerInvariant()
    $Approved += [pscustomobject]@{ file=$Relative; sha256=$Hash; bytes=$File.Length; truth_status='CAPTURED_ARTIFACT_NOT_OUTCOME_PROOF' }
}

if ($Rejected.Count -gt 0) {
    $BlockedReport = Join-Path $ControlCenterRoot ('data\blocked_submissions\' + $SessionId + '_BLOCKED.json')
    New-Item -ItemType Directory -Path (Split-Path $BlockedReport -Parent) -Force | Out-Null
    @{ session_id=$SessionId; rejected=$Rejected; held=$Held; status='BLOCKED_NO_PUSH' } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $BlockedReport -Encoding UTF8
    Remove-Item -LiteralPath $Target -Force -Recurse -ErrorAction SilentlyContinue
    throw 'Automatic capture blocked: prohibited or sensitive automatic-capture file detected.'
}
if ($Approved.Count -eq 0) {
    Remove-Item -LiteralPath $Target -Force -Recurse -ErrorAction SilentlyContinue
    Write-Host 'No approved artifacts to submit. Held outputs remain outside automatic capture.' -ForegroundColor Yellow
    exit 0
}

$CapturedAt = (Get-Date).ToUniversalTime().ToString('o')
@{ session_id=$SessionId; captured_at_utc=$CapturedAt; branch=$CaptureBranch; truth_status='AUTOMATIC_CAPTURED_ARTIFACTS_NOT_OUTCOME_PROOF'; approved_files=$Approved; held_files=$Held } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $Target 'capture_manifest.json') -Encoding UTF8
$Ledger = Join-Path $RepoRoot 'APEX\runtime-captures\CAPTURE_LEDGER.jsonl'
New-Item -ItemType Directory -Path (Split-Path $Ledger -Parent) -Force | Out-Null
(@{ session_id=$SessionId; captured_at_utc=$CapturedAt; approved_count=$Approved.Count; held_count=$Held.Count; branch=$CaptureBranch } | ConvertTo-Json -Compress) | Add-Content -LiteralPath $Ledger -Encoding UTF8

& git -C $RepoRoot add -- 'APEX/runtime-captures'
$Pending = (& git -C $RepoRoot status --porcelain -- 'APEX/runtime-captures') -join ''
if ([string]::IsNullOrWhiteSpace($Pending)) { Write-Host 'No new capture changes to commit.'; exit 0 }
& git -C $RepoRoot commit -m ('capture(arx): preserve execution cycle ' + $SessionId)
if ($LASTEXITCODE -ne 0) { throw 'Commit failed. Capture remains local only.' }
& git -C $RepoRoot push origin $CaptureBranch
if ($LASTEXITCODE -ne 0) { throw 'Push failed. Do not claim repository preservation.' }
$CommitSha = (& git -C $RepoRoot rev-parse HEAD).Trim()
Write-Host ('AUTO CAPTURE PUSHED: ' + $CommitSha) -ForegroundColor Green
Write-Host ('Approved files: ' + $Approved.Count + '; held files: ' + $Held.Count) -ForegroundColor Green
