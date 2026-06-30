param(
    [string]$CsvPath,
    [switch]$NoPublish
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$PrivateSourceDir = Join-Path $Root "private-source-data"
$TargetCsv = Join-Path $PrivateSourceDir "GLA_2026_Registration_Outreach_Tracking.csv"
$PublicDir = Join-Path $Root "github-pages"
$LogDir = Join-Path $Root "logs"
$LogPath = Join-Path $LogDir "dashboard-update.log"
$LiveUrl = "https://ninarhop.github.io/GLA-Dashboard/"
$BundledPython = "C:\Users\nina\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

New-Item -ItemType Directory -Force -Path $PrivateSourceDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Set-Location $Root

function Write-Step {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    $line | Tee-Object -FilePath $LogPath -Append
}

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Command
    )
    Write-Step "Starting: $Name"
    & $Command 2>&1 | Tee-Object -FilePath $LogPath -Append
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
    Write-Step "Finished: $Name"
}

function Get-PythonRunner {
    $candidates = @(
        @{ Command = "python"; Prefix = @() },
        @{ Command = "py"; Prefix = @("-3") },
        @{ Command = $BundledPython; Prefix = @() }
    )

    foreach ($candidate in $candidates) {
        $command = $candidate.Command
        if (-not (Get-Command $command -ErrorAction SilentlyContinue) -and -not (Test-Path -LiteralPath $command)) {
            continue
        }
        try {
            & $command @($candidate.Prefix) --version 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) {
                return $candidate
            }
        } catch {
            continue
        }
    }

    throw "Python was not found. Install Python or run this from the Codex workspace where bundled Python is available."
}

function Invoke-Python {
    param([string[]]$Arguments)
    & $script:PythonRunner.Command @($script:PythonRunner.Prefix) @Arguments
}

function Select-CsvFile {
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = [System.Windows.Forms.OpenFileDialog]::new()
    $dialog.Title = "Select the updated GLA tracking CSV"
    $dialog.Filter = "CSV files (*.csv)|*.csv|All files (*.*)|*.*"
    $dialog.Multiselect = $false
    $result = $dialog.ShowDialog()
    if ($result -ne [System.Windows.Forms.DialogResult]::OK) {
        throw "No CSV selected. Update canceled."
    }
    return $dialog.FileName
}

function Publish-ToGhPages {
    $publishPath = Join-Path $env:TEMP "gla-dashboard-gh-pages-publish"
    $tempRoot = [System.IO.Path]::GetFullPath($env:TEMP)
    $publishFullPath = [System.IO.Path]::GetFullPath($publishPath)
    if (-not $publishFullPath.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to clean unexpected publish path: $publishFullPath"
    }

    if (Test-Path -LiteralPath $publishPath) {
        git worktree remove --force $publishPath 2>$null
        if (Test-Path -LiteralPath $publishPath) {
            Remove-Item -LiteralPath $publishPath -Recurse -Force
        }
    }

    Invoke-Step "Fetch gh-pages" { git fetch origin gh-pages }
    Invoke-Step "Create temporary gh-pages worktree" { git worktree add --detach $publishPath origin/gh-pages }

    Get-ChildItem -Force -LiteralPath $PublicDir | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $publishPath -Recurse -Force
    }

    Invoke-Step "Stage live GitHub Pages files" { git -C $publishPath add --all }
    $changes = git -C $publishPath status --porcelain
    if ($changes) {
        $message = "Publish dashboard aggregates {0}" -f (Get-Date -Format "yyyy-MM-dd HH:mm")
        Invoke-Step "Commit live GitHub Pages files" { git -C $publishPath commit -m $message }
        Invoke-Step "Push live GitHub Pages branch" { git -C $publishPath push origin HEAD:gh-pages }
    } else {
        Write-Step "No live GitHub Pages changes to publish."
    }

    git worktree remove --force $publishPath 2>$null
}

try {
    Write-Step "Dashboard update started."
    $script:PythonRunner = Get-PythonRunner
    Write-Step "Using Python: $($script:PythonRunner.Command)"

    if (-not $CsvPath) {
        $CsvPath = Select-CsvFile
    }

    $sourceCsv = [System.IO.Path]::GetFullPath($CsvPath)
    if (-not (Test-Path -LiteralPath $sourceCsv)) {
        throw "CSV not found: $sourceCsv"
    }
    if ([System.IO.Path]::GetExtension($sourceCsv).ToLowerInvariant() -ne ".csv") {
        throw "Selected file is not a CSV: $sourceCsv"
    }

    Write-Step "Copying selected CSV to $TargetCsv"
    Copy-Item -LiteralPath $sourceCsv -Destination $TargetCsv -Force

    Invoke-Step "Build public aggregate dashboard JSON" { Invoke-Python @("scripts\build_public_dashboard.py") }
    Invoke-Step "Validate public output privacy" { Invoke-Python @("scripts\validate_public_output.py", "--public-dir", $PublicDir) }

    $mainChanges = git status --porcelain -- github-pages
    if ($mainChanges) {
        Invoke-Step "Stage aggregate public output on main" { git add github-pages }
        Invoke-Step "Commit aggregate public output on main" { git commit -m "Update public dashboard aggregates [skip ci]" }
        Invoke-Step "Push main backup copy" { git push origin main }
    } else {
        Write-Step "No aggregate public output changes on main."
    }

    if (-not $NoPublish) {
        Publish-ToGhPages
    } else {
        Write-Step "Skipping live publish because -NoPublish was provided."
    }

    Write-Step "Dashboard update complete."
    Write-Host ""
    Write-Host "Dashboard update complete." -ForegroundColor Green
    Write-Host "Live site: $LiveUrl" -ForegroundColor Cyan
    Write-Host "Log file: $LogPath"
} catch {
    Write-Step "Dashboard update failed: $($_.Exception.Message)"
    Write-Host ""
    Write-Host "Dashboard update failed." -ForegroundColor Red
    Write-Host $_.Exception.Message
    Write-Host "Log file: $LogPath"
    exit 1
}
