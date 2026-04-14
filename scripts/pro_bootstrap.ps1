param(
    [Parameter(Mandatory = $true)]
    [string]$RepoUrl,

    [string]$LocalPath = ".",
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"

function Ensure-Git {
    $git = Get-Command git -ErrorAction SilentlyContinue
    if (-not $git) {
        throw "git is not installed or not on PATH."
    }
}

Ensure-Git

if (-not (Test-Path $LocalPath)) {
    New-Item -ItemType Directory -Path $LocalPath | Out-Null
}

Set-Location $LocalPath

if (-not (Test-Path ".git")) {
    if ((Get-ChildItem -Force | Measure-Object).Count -eq 0) {
        Write-Host "Cloning into empty directory..." -ForegroundColor Cyan
        git clone $RepoUrl .
    }
    else {
        Write-Host "Initializing git in existing directory..." -ForegroundColor Cyan
        git init
        git remote add origin $RepoUrl
    }
}

$remote = git remote 2>$null
if (-not ($remote -match "origin")) {
    git remote add origin $RepoUrl
}

Write-Host "Fetching remote branch info..." -ForegroundColor Cyan
git fetch origin

$currentBranch = (git branch --show-current).Trim()
if (-not $currentBranch) {
    git checkout -b $Branch
}
elseif ($currentBranch -ne $Branch) {
    git checkout $Branch 2>$null
    if ($LASTEXITCODE -ne 0) {
        git checkout -b $Branch
    }
}

# Set upstream if branch exists remotely.
git rev-parse --verify origin/$Branch 2>$null
if ($LASTEXITCODE -eq 0) {
    git branch --set-upstream-to=origin/$Branch $Branch 2>$null
}

Write-Host "Bootstrap complete." -ForegroundColor Green
Write-Host "Repo: $(git remote get-url origin)" -ForegroundColor Green
Write-Host "Branch: $(git branch --show-current)" -ForegroundColor Green
