$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $Root
$Port = 8765
Write-Host "Dream Draw / Value Compass MVP starting at http://localhost:$Port/" -ForegroundColor Cyan
Write-Host "Close this PowerShell window to stop the local server." -ForegroundColor Yellow
Start-Process "http://localhost:$Port/"
python -m http.server $Port
