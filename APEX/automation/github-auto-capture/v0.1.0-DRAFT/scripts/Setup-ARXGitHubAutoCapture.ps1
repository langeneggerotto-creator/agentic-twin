[CmdletBinding()]
param(
    [string]$ControlCenterRoot = 'C:\Users\lange\Dropbox\Online Businesses\APEX Systems\Documentation\Learning System\CONTROL_CENTER',
    [string]$RepositoryUrl = 'https://github.com/langeneggerotto-creator/agentic-twin.git',
    [string]$CaptureBranch = 'arx-autonomous-capture'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

Write-Host 'APEX ARX GitHub Auto-Capture - One-Time Setup' -ForegroundColor Yellow
$Git = Get-Command git -ErrorAction SilentlyContinue
if ($null -eq $Git) { throw 'Git is not installed or not on PATH. Install Git for Windows first.' }

$Gh = Get-Command gh -ErrorAction SilentlyContinue
if ($null -eq $Gh) {
    Write-Host 'GitHub CLI not found. Installing with winget...' -ForegroundColor Yellow
    winget install --id GitHub.cli -e --source winget
    throw 'GitHub CLI installation started. Open a new PowerShell window, then run setup again.'
}

& gh auth status 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host 'One-time GitHub authorization required. Follow the browser sign-in prompt.' -ForegroundColor Cyan
    & gh auth login --hostname github.com --git-protocol https --web
}
& gh auth setup-git

$RepoRoot = Join-Path $ControlCenterRoot 'github\agentic-twin'
$RepoParent = Split-Path $RepoRoot -Parent
New-Item -ItemType Directory -Path $RepoParent -Force | Out-Null

if (-not (Test-Path (Join-Path $RepoRoot '.git'))) {
    & git clone $RepositoryUrl $RepoRoot
} else {
    & git -C $RepoRoot fetch origin --prune
}

& git -C $RepoRoot fetch origin --prune
$RemoteCaptureBranch = (& git -C $RepoRoot branch -r --list ("origin/" + $CaptureBranch))
if (-not [string]::IsNullOrWhiteSpace($RemoteCaptureBranch)) {
    & git -C $RepoRoot checkout -B $CaptureBranch ("origin/" + $CaptureBranch)
    & git -C $RepoRoot branch --set-upstream-to=("origin/" + $CaptureBranch) $CaptureBranch
} else {
    & git -C $RepoRoot checkout main
    & git -C $RepoRoot pull --ff-only origin main
    & git -C $RepoRoot checkout -b $CaptureBranch
    & git -C $RepoRoot push -u origin $CaptureBranch
}

Write-Host 'Setup complete.' -ForegroundColor Green
Write-Host ("Repository clone: {0}" -f $RepoRoot) -ForegroundColor Green
Write-Host ("Automatic capture branch: {0}" -f $CaptureBranch) -ForegroundColor Green
Write-Host 'Routine ARX captures can now push to GitHub without manual submission.' -ForegroundColor Green
