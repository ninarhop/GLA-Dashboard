param(
    [string]$InstallFolder = "$HOME\GLA-Dashboard-Code"
)

$ErrorActionPreference = "Stop"

$Desktop = [Environment]::GetFolderPath("Desktop")
$LauncherPath = Join-Path $Desktop "Refresh GLA Dashboard.ps1"
$RefreshScript = Join-Path $InstallFolder "scripts\run_local_refresh.ps1"

$LauncherContent = @"
`$ErrorActionPreference = "Stop"

Set-Location "$InstallFolder"

Write-Host "Updating dashboard code..."
git pull origin platform-v1

Write-Host ""
Write-Host "Checking GLA intake files..."
& "$RefreshScript"

Write-Host ""
Read-Host "Press Enter to close"
"@

Set-Content -LiteralPath $LauncherPath -Value $LauncherContent -Encoding UTF8

Write-Host "Created desktop launcher:"
Write-Host $LauncherPath
