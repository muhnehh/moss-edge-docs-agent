$ErrorActionPreference = "Stop"

$legacyFiles = @(
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "package-lock.json",
    "package.json",
    "pnpm-lock.yaml",
    "ROADMAP.md",
    "SECURITY.md"
)

$legacyDirs = @(
    "apps",
    "assets",
    "benchmarks",
    "examples",
    "packages",
    "sdks"
)

foreach ($file in $legacyFiles) {
    if (Test-Path $file) {
        Remove-Item -LiteralPath $file -Force
        Write-Host "Removed file: $file"
    }
}

foreach ($dir in $legacyDirs) {
    if (Test-Path $dir) {
        Remove-Item -LiteralPath $dir -Recurse -Force
        Write-Host "Removed directory: $dir"
    }
}

Write-Host "Legacy upstream content cleanup complete." -ForegroundColor Green
