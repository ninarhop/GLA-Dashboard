param(
    [string]$InstallFolder = "$HOME\GLA-Dashboard-Code",
    [string]$Branch = "platform-v1"
)

$ErrorActionPreference = "Stop"
$RepositoryUrl = "https://github.com/ninarhop/GLA-Dashboard.git"

Write-Host ""
Write-Host "GLA Dashboard Windows Setup"
Write-Host "Code folder: $InstallFolder"
Write-Host "Branch: $Branch"
Write-Host ""

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git is not installed or is not available in PowerShell."
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python is not installed or is not available in PowerShell."
}

if (Test-Path -LiteralPath (Join-Path $InstallFolder ".git")) {
    Write-Host "[FOUND] Existing local project"

    Push-Location $InstallFolder
    try {
        git fetch origin
        git checkout $Branch
        git pull origin $Branch
    }
    finally {
        Pop-Location
    }
}
else {
    if (Test-Path -LiteralPath $InstallFolder) {
        $ExistingItems = Get-ChildItem -LiteralPath $InstallFolder -Force

        if ($ExistingItems.Count -gt 0) {
            throw "The installation folder exists and is not empty: $InstallFolder"
        }
    }

    git clone --branch $Branch --single-branch $RepositoryUrl $InstallFolder
}

$Requirements = Join-Path $InstallFolder "requirements.txt"

if (Test-Path -LiteralPath $Requirements) {
    Write-Host ""
    Write-Host "Installing required Python packages..."
    python -m pip install -r $Requirements
}

$RefreshScript = Join-Path $InstallFolder "scripts\run_local_refresh.ps1"

if (-not (Test-Path -LiteralPath $RefreshScript)) {
    throw "Local refresh script was not found: $RefreshScript"
}

Write-Host ""
Write-Host "Running the first intake-file check..."
& $RefreshScript

Write-Host ""
Write-Host "Windows setup completed."
Write-Host "Your private data remains on the G: drive."
Write-Host "Your local code is stored at:"
Write-Host $InstallFolder
