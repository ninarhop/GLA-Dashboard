param(
    [string]$DataRoot = "G:\Shared drives\Get Loud Arkansas\Data\Get Load Arkansas Dashboard"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "GLA Dashboard Local Refresh"
Write-Host "Data root: $DataRoot"
Write-Host ""

if (-not (Test-Path -LiteralPath $DataRoot)) {
    throw "The Google Drive data folder was not found: $DataRoot"
}

$RequiredFolders = @(
    "01_Data_Intake\01_Current_VRVH",
    "01_Data_Intake\02_Purge_Lists",
    "01_Data_Intake\03_EZ_App",
    "01_Data_Intake\04_Outreach",
    "01_Data_Intake\05_Priority_Counties"
)

foreach ($RelativeFolder in $RequiredFolders) {
    $FullFolder = Join-Path $DataRoot $RelativeFolder

    if (-not (Test-Path -LiteralPath $FullFolder)) {
        throw "Required intake folder is missing: $FullFolder"
    }

    Write-Host "[FOUND FOLDER] $FullFolder"
}

$ConfigExample = Join-Path $PSScriptRoot "..\config\data_sources.example.json"
$LocalConfig = Join-Path $PSScriptRoot "..\config\data_sources.local.json"

if (-not (Test-Path -LiteralPath $LocalConfig)) {
    Copy-Item -LiteralPath $ConfigExample -Destination $LocalConfig
    Write-Host "[CREATED] Local configuration file"
}

Write-Host ""
Write-Host "Checking for the newest intake files..."
python (Join-Path $PSScriptRoot "find_latest_sources.py")

if ($LASTEXITCODE -ne 0) {
    throw "The source-file check failed."
}

Write-Host ""
Write-Host "Source check completed."
Write-Host "No private files were uploaded to GitHub."
