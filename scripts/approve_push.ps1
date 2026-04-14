param(
    [string]$Remote = "origin",
    [string]$Branch = "main",
    [string]$CommitMessage = "",
    [switch]$SkipPull
)

$ErrorActionPreference = "Stop"

function Confirm-Yes([string]$Prompt) {
    $answer = Read-Host $Prompt
    return $answer -match '^(y|yes)$'
}

if (-not (Test-Path ".git")) {
    Write-Host "Not a git repository in current directory." -ForegroundColor Red
    exit 1
}

Write-Host "\n=== Current Branch ===" -ForegroundColor Cyan
git branch --show-current

Write-Host "\n=== Git Status ===" -ForegroundColor Cyan
git status --short

$changes = git status --porcelain
if ($changes) {
    if (-not (Confirm-Yes "\nStage all local changes now? (y/n)")) {
        Write-Host "Cancelled by user before staging." -ForegroundColor Yellow
        exit 0
    }

    git add -A

    Write-Host "\n=== Staged Diff Summary ===" -ForegroundColor Cyan
    git diff --cached --stat

    if (-not $CommitMessage) {
        $CommitMessage = Read-Host "\nEnter commit message"
    }

    if (-not $CommitMessage) {
        Write-Host "Commit message cannot be empty." -ForegroundColor Red
        exit 1
    }

    if (-not (Confirm-Yes "\nCreate commit '$CommitMessage'? (y/n)")) {
        Write-Host "Cancelled by user before commit." -ForegroundColor Yellow
        exit 0
    }

    git commit -m $CommitMessage
}
else {
    Write-Host "\nNo local file changes detected." -ForegroundColor Yellow
}

if (-not $SkipPull) {
    if (Confirm-Yes "\nPull latest changes with rebase before push? (y/n)") {
        git pull --rebase $Remote $Branch
    }
}

Write-Host "\n=== Last Commit ===" -ForegroundColor Cyan
git log -1 --oneline

if (-not (Confirm-Yes "\nPush current HEAD to $Remote/$Branch ? (y/n)")) {
    Write-Host "Push cancelled by user." -ForegroundColor Yellow
    exit 0
}

git push $Remote HEAD:$Branch
Write-Host "Push complete." -ForegroundColor Green
