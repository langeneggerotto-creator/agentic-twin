[CmdletBinding()]
param(
    [int]$IntervalMinutes = 5,
    [string]$ControlCenterRoot = 'C:\Users\lange\Dropbox\Online Businesses\APEX Systems\Documentation\Learning System\CONTROL_CENTER',
    [string]$RepositoryUrl = 'https://github.com/langeneggerotto-creator/agentic-twin.git',
    [string]$CaptureBranch = 'arx-autonomous-capture'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if ($IntervalMinutes -lt 5) { throw 'IntervalMinutes must be at least 5.' }
Write-Host 'APEX GitHub Auto-Capture v0.2 — Unattended Safe Submission Setup' -ForegroundColor Yellow
Write-Host 'One-time account authorization may be requested by GitHub when this machine is not already authenticated.' -ForegroundColor Cyan

New-Item -ItemType Directory -LiteralPath $ControlCenterRoot -Force | Out-Null
foreach ($Relative in @('auto_capture_inbox','auto_capture_processing','auto_capture_processed','auto_capture_held','data\auto_capture_logs','github')) {
    New-Item -ItemType Directory -LiteralPath (Join-Path $ControlCenterRoot $Relative) -Force | Out-Null
}

$Git = Get-Command git -ErrorAction SilentlyContinue
if ($null -eq $Git) { throw 'Git is not installed or is not available on PATH.' }
$Gh = Get-Command gh -ErrorAction SilentlyContinue
if ($null -eq $Gh) { throw 'GitHub CLI is not installed or is not available on PATH. Install GitHub CLI, then run this installer again.' }

& gh auth status 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host 'GitHub authentication is required once on this machine. Complete the secure GitHub sign-in window when it opens.' -ForegroundColor Yellow
    & gh auth login --hostname github.com --git-protocol https --web
    if ($LASTEXITCODE -ne 0) { throw 'GitHub authorization was not completed. Automation was not activated.' }
}
& gh auth setup-git
if ($LASTEXITCODE -ne 0) { throw 'GitHub credential helper setup did not complete.' }

$RepoRoot = Join-Path $ControlCenterRoot 'github\agentic-twin'
if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot '.git'))) {
    & git clone --branch $CaptureBranch --single-branch $RepositoryUrl $RepoRoot
    if ($LASTEXITCODE -ne 0) { throw 'Repository clone failed. Automation was not activated.' }
} else {
    & git -C $RepoRoot fetch origin --prune
    & git -C $RepoRoot checkout $CaptureBranch
    & git -C $RepoRoot pull --ff-only origin $CaptureBranch
    if ($LASTEXITCODE -ne 0) { throw 'Repository synchronization failed. Automation was not activated.' }
}

$SweepRunner = Join-Path $RepoRoot 'APEX\automation\github-auto-capture\v0.2.0-DRAFT\scripts\Invoke-APEXAutoCaptureSweep.ps1'
if (-not (Test-Path -LiteralPath $SweepRunner)) { throw "Sweep runner was not found in repository clone: $SweepRunner" }

$TaskName = 'APEX_GitHub_Unattended_Safe_Capture'
$Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$SweepRunner`" -ControlCenterRoot `"$ControlCenterRoot`""
$Action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $Arguments
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description 'APEX governed unattended software artifact capture to GitHub.' -Force | Out-Null

$ActivationReceipt = [ordered]@{
    artifact_id = 'APEX-GITHUB-AUTO-CAPTURE-ACTIVATION-003'
    activated_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    branch = $CaptureBranch
    task_name = $TaskName
    interval_minutes = $IntervalMinutes
    status = 'UNATTENDED_SAFE_SUBMISSION_SCHEDULED'
    boundary = 'Safe artifact capture only. Gated/private/physical/production actions remain blocked.'
}
$ReceiptPath = Join-Path $ControlCenterRoot 'data\auto_capture_logs\ACTIVATION_RECEIPT.json'
$ActivationReceipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $ReceiptPath -Encoding UTF8

Write-Host 'APEX unattended GitHub safe-capture is scheduled.' -ForegroundColor Green
Write-Host ("Watch folder: {0}" -f (Join-Path $ControlCenterRoot 'auto_capture_inbox')) -ForegroundColor Green
Write-Host ("Branch: {0}" -f $CaptureBranch) -ForegroundColor Green
Write-Host ("Activation receipt: {0}" -f $ReceiptPath) -ForegroundColor Green
Write-Host 'Place eligible artifacts in the inbox through the staging command; capture proceeds automatically.' -ForegroundColor Cyan
Write-Host 'No physical action, deployment, private-media upload or main-branch promotion is authorized.' -ForegroundColor Yellow
