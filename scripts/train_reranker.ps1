param(
    [string]$TrainingData = "data/train_pairs.sample.jsonl",
    [int]$Epochs = 2,
    [int]$BatchSize = 16,
    [string]$ModelId = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    [string]$OutputDir = "reranker/models/reranker_finetuned"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
    py -m venv .venv
}

$python = ".\.venv\Scripts\python.exe"
& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt

& $python -m reranker.train_reranker `
    --data-path $TrainingData `
    --epochs $Epochs `
    --batch-size $BatchSize `
    --model-id $ModelId `
    --output-dir $OutputDir

& $python -m reranker.export_to_onnx --source-model $OutputDir

Write-Host "Training + ONNX export complete." -ForegroundColor Green
