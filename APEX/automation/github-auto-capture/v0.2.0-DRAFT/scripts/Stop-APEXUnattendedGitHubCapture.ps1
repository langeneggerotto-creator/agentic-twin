[CmdletBinding()]
param(
    [string]$ControlCenterRoot = 'C:\Users\lange\Dropbox\Online Businesses\APEX Systems\Documentation\Learning System\CONTROL_CENTER',
    [switch]$PreserveLocalInbox
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$TaskName = 'APEX_GitHub_Unattended_Safe_Capture'
$Task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($null -ne $Task) {
    Disable-ScheduledTask -TaskName $TaskName | Out-Null
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host ("Stopped and removed scheduled task: {0}" -f $TaskName) -ForegroundColor Yellow
} else {
    Write-Host ("No installed scheduled task found: {0}" -f $TaskName) -ForegroundColor Cyan
}

$Logs = Join-Path $ControlCenterRoot 'data\auto_capture_logs'
New-Item -ItemType Directory -LiteralPath $Logs -Force | Out-Null
$Receipt = [ordered]@{
    artifact_id = 'APEX-GITHUB-AUTO-CAPTURE-ACTIVATION-003'
    stopped_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    task_name = $TaskName
    status = 'UNATTENDED_CAPTURE_STOPPED'
    preserve_local_inbox = [bool]$PreserveLocalInbox
    boundary = 'Stopping scheduled capture does not remove repository history.'
}
$ReceiptPath = Join-Path $Logs 'STOP_RECEIPT.json'
$Receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $ReceiptPath -Encoding UTF8

if (-not $PreserveLocalInbox) {
    Write-Host 'Existing inbox/held/processed artifact folders are retained by default for evidence preservation.' -ForegroundColor Cyan
}
Write-Host ("Stop receipt: {0}" -f $ReceiptPath) -ForegroundColor Green
