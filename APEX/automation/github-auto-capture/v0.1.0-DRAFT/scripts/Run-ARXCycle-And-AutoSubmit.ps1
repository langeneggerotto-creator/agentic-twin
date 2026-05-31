[CmdletBinding()]
param(
    [string]$ControlCenterRoot = 'C:\Users\lange\Dropbox\Online Businesses\APEX Systems\Documentation\Learning System\CONTROL_CENTER'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$SessionId = 'ARX-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
$Scripts = Join-Path $ControlCenterRoot 'scripts'
$CaptureSource = Join-Path $ControlCenterRoot 'auto_capture_outbox'
$RunCycle = Join-Path $Scripts 'run_cycle.ps1'
if (-not (Test-Path -LiteralPath $RunCycle)) { throw "ARX run-cycle script not found: $RunCycle" }

& $RunCycle

Remove-Item -LiteralPath $CaptureSource -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $CaptureSource -Force | Out-Null
foreach ($Relative in @('reports','manifests','data\exports','dashboard')) {
    $Source = Join-Path $ControlCenterRoot $Relative
    if (Test-Path -LiteralPath $Source) {
        $Dest = Join-Path $CaptureSource $Relative
        New-Item -ItemType Directory -Path (Split-Path $Dest -Parent) -Force | Out-Null
        Copy-Item -LiteralPath $Source -Destination $Dest -Recurse -Force
    }
}

$Submitter = Join-Path $PSScriptRoot 'Invoke-ARXGitHubAutoSubmit.ps1'
& $Submitter -SourcePath $CaptureSource -SessionId $SessionId -ControlCenterRoot $ControlCenterRoot
Remove-Item -LiteralPath $CaptureSource -Recurse -Force -ErrorAction SilentlyContinue
Write-Host 'ARX cycle complete; approved safe artifacts submitted; proceed to recalculated next target.' -ForegroundColor Green
