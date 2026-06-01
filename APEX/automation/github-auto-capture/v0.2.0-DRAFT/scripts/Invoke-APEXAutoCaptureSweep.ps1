[CmdletBinding()]
param(
    [string]$ControlCenterRoot = 'C:\Users\lange\Dropbox\Online Businesses\APEX Systems\Documentation\Learning System\CONTROL_CENTER',
    [int]$StableFileAgeSeconds = 20,
    [int]$MaxBatchesPerSweep = 20
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Inbox = Join-Path $ControlCenterRoot 'auto_capture_inbox'
$Processing = Join-Path $ControlCenterRoot 'auto_capture_processing'
$Processed = Join-Path $ControlCenterRoot 'auto_capture_processed'
$Held = Join-Path $ControlCenterRoot 'auto_capture_held'
$Logs = Join-Path $ControlCenterRoot 'data\auto_capture_logs'
foreach ($Path in @($Inbox, $Processing, $Processed, $Held, $Logs)) {
    New-Item -ItemType Directory -LiteralPath $Path -Force | Out-Null
}

$ExistingSubmitter = Join-Path $ControlCenterRoot 'github\agentic-twin\APEX\automation\github-auto-capture\v0.1.0-DRAFT\scripts\Invoke-ARXGitHubAutoSubmit.ps1'
if (-not (Test-Path -LiteralPath $ExistingSubmitter)) {
    throw "Automatic submitter is not installed locally: $ExistingSubmitter. Run the installer once."
}

$SweepId = 'SWEEP-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
$SweepLog = [ordered]@{
    sweep_id = $SweepId
    started_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    status = 'RUNNING'
    processed_batches = @()
    held_batches = @()
    ignored_batches = @()
}

$Candidates = @(Get-ChildItem -LiteralPath $Inbox -Directory -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -First $MaxBatchesPerSweep)
foreach ($Batch in $Candidates) {
    $NewestFile = Get-ChildItem -LiteralPath $Batch.FullName -File -Recurse -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($null -eq $NewestFile) {
        $SweepLog.ignored_batches += [ordered]@{ batch = $Batch.Name; reason = 'EMPTY_BATCH' }
        continue
    }
    $Age = ((Get-Date) - $NewestFile.LastWriteTime).TotalSeconds
    if ($Age -lt $StableFileAgeSeconds) {
        $SweepLog.ignored_batches += [ordered]@{ batch = $Batch.Name; reason = 'WAITING_FOR_STABLE_WRITE' }
        continue
    }

    $WorkPath = Join-Path $Processing $Batch.Name
    Move-Item -LiteralPath $Batch.FullName -Destination $WorkPath -Force
    try {
        $SessionId = 'AUTO-' + $Batch.Name
        & $ExistingSubmitter -SourcePath $WorkPath -SessionId $SessionId -ControlCenterRoot $ControlCenterRoot
        $Destination = Join-Path $Processed $Batch.Name
        Move-Item -LiteralPath $WorkPath -Destination $Destination -Force
        $SweepLog.processed_batches += [ordered]@{
            batch = $Batch.Name
            status = 'SUBMITTED_TO_GOVERNED_BRANCH'
            local_archive = $Destination
        }
    } catch {
        $Destination = Join-Path $Held $Batch.Name
        Move-Item -LiteralPath $WorkPath -Destination $Destination -Force -ErrorAction SilentlyContinue
        $HoldReceipt = [ordered]@{
            batch = $Batch.Name
            status = 'HELD_NO_AUTOMATIC_SUBMISSION_CLAIM'
            reason = $_.Exception.Message
            held_at_utc = (Get-Date).ToUniversalTime().ToString('o')
        }
        $HoldReceipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $Destination 'hold_receipt.json') -Encoding UTF8
        $SweepLog.held_batches += $HoldReceipt
    }
}

$SweepLog.status = 'COMPLETED'
$SweepLog.completed_at_utc = (Get-Date).ToUniversalTime().ToString('o')
$LogPath = Join-Path $Logs ($SweepId + '.json')
$SweepLog | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $LogPath -Encoding UTF8
Write-Host ("Automatic capture sweep complete: {0} submitted; {1} held; {2} waiting/empty." -f $SweepLog.processed_batches.Count, $SweepLog.held_batches.Count, $SweepLog.ignored_batches.Count) -ForegroundColor Green
Write-Host ("Sweep log: {0}" -f $LogPath) -ForegroundColor Cyan
