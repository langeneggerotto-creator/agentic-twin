[CmdletBinding()]
param(
    [int]$IntervalMinutes = 60,
    [string]$ControlCenterRoot = 'C:\Users\lange\Dropbox\Online Businesses\APEX Systems\Documentation\Learning System\CONTROL_CENTER'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if ($IntervalMinutes -lt 15) { throw 'IntervalMinutes must be at least 15 for the bounded software-only capture loop.' }
$Runner = Join-Path $PSScriptRoot 'Run-ARXCycle-And-AutoSubmit.ps1'
if (-not (Test-Path -LiteralPath $Runner)) { throw "Runner not found: $Runner" }
$TaskName = 'APEX_ARX_Cycle_And_GitHub_AutoCapture'
$Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`" -ControlCenterRoot `"$ControlCenterRoot`""
$Action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $Arguments
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description 'APEX ARX governed software cycle with automatic GitHub capture.' -Force | Out-Null
Write-Host ("Installed scheduled ARX cycle and GitHub auto-capture every {0} minutes." -f $IntervalMinutes) -ForegroundColor Green
Write-Host 'Physical autonomy remains locked; this runs software/report capture only.' -ForegroundColor Yellow
