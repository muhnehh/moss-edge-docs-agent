param(
    [switch]$SkipExport,
    [switch]$SkipIndex,
    [switch]$SkipBenchmark,
    [switch]$TrainReranker,
    [string]$TrainingData = "data/train_pairs.sample.jsonl"
)

$ErrorActionPreference = "Stop"

function Get-EnvValue([string]$Key) {
    $line = Select-String -Path ".env" -Pattern "^$Key=(.*)$" | Select-Object -First 1
    if (-not $line) {
        return ""
    }
    return $line.Matches[0].Groups[1].Value.Trim()
}

if (-not (Test-Path ".venv")) {
    py -m venv .venv
}

$python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Virtual environment python executable not found at $python"
}

& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt

if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
    Write-Host "Created .env from .env.example. Fill required keys before continuing." -ForegroundColor Yellow
    exit 0
}

if ($TrainReranker) {
    & $python -m reranker.train_reranker --data-path $TrainingData --output-dir reranker/models/reranker_finetuned
}

if (-not $SkipExport) {
    if ($TrainReranker) {
        & $python -m reranker.export_to_onnx --source-model reranker/models/reranker_finetuned
    }
    else {
        & $python -m reranker.export_to_onnx
    }
}

if ((-not $SkipIndex -or -not $SkipBenchmark) -and ((Get-EnvValue "MOSS_PROJECT_ID") -eq "" -or (Get-EnvValue "MOSS_PROJECT_KEY") -eq "")) {
    Write-Host "MOSS_PROJECT_ID and MOSS_PROJECT_KEY are required in .env to run index/benchmark." -ForegroundColor Red
    exit 1
}

if (-not $SkipIndex) {
    & $python -m moss_integration.moss_indexer
}

if (-not $SkipBenchmark) {
    & $python -m metrics.benchmark
    Write-Host "Pipeline complete. Review metrics/results/benchmark.json" -ForegroundColor Green
}
else {
    Write-Host "Pipeline complete. Benchmark skipped." -ForegroundColor Green
}
