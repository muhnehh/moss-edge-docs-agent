param(
    [Parameter(Mandatory=$true)][string]$GitHubRepoUrl,
    [string]$DefaultBranch = "main"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".git")) {
    git init
}

git add .
git commit -m "chore: bootstrap moss edge docs agent"

git branch -M $DefaultBranch
git remote remove origin 2>$null

git remote add origin $GitHubRepoUrl
git push -u origin $DefaultBranch

Write-Host "Repository initialized and remote configured." -ForegroundColor Green
