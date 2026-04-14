# moss-edge-docs-agent

A production-style edge retrieval agent using Moss for retrieval and an ONNX reranker for local ranking and routing.

## A to Z Build Status

This repository now includes the full implementation path:

- corpus indexing over Moss docs
- retrieval wrapper over Moss SDK
- cross-encoder reranker fine-tuning
- ONNX export + INT8 quantization
- reranking + routing in agent loop
- optional voice in and voice out flow
- benchmark reporting and test coverage
- CI quality checks and approval-gated git push flow

## What This Project Demonstrates

- Sub-10ms retrieval path using Moss index runtime.
- Local ONNX cross-encoder reranking for better precision.
- Query routing that avoids unnecessary cloud calls.
- Reproducible benchmark reporting with latency metrics.

## Architecture

question -> Moss retrieval -> ONNX rerank -> route

- local extractive answer path when confidence is high
- cloud fallback path when confidence is low

## Quickstart

1. Open PowerShell in the project root.
2. Run the full bootstrap pipeline script:

```powershell
pwsh ./scripts/run_full_pipeline.ps1
```

3. If `.env` is created for the first time, add your keys and rerun the script:

- `MOSS_PROJECT_ID`
- `MOSS_PROJECT_KEY`
- `OPENAI_API_KEY`

4. Run interactive chat after setup:

```powershell
.\.venv\Scripts\python.exe -m agent.chat_agent
```

5. Optional: run full voice flow with an input audio file:

```powershell
pwsh ./scripts/run_voice_agent.ps1 -InputAudio data/sample_question.wav
```

## Manual Commands (Optional)

1. Create and activate Python 3.11+ environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy env file and set keys:

```bash
cp .env.example .env
```

4. Build index:

```bash
python -m moss_integration.moss_indexer
```

5. Run chat loop:

```bash
python -m agent.chat_agent
```

6. Run benchmark:

```bash
python -m metrics.benchmark
```

7. Run tests:

```bash
pytest
```

## Reranker Training and Export

Train a reranker on your own labeled pairs, then export and quantize:

```powershell
pwsh ./scripts/train_reranker.ps1
```

Or run manually:

```bash
python -m reranker.train_reranker --data-path data/train_pairs.sample.jsonl --output-dir reranker/models/reranker_finetuned
python -m reranker.export_to_onnx --source-model reranker/models/reranker_finetuned
```

Training data format uses JSONL with fields:

- query
- positive or positives
- negatives

See sample file: data/train_pairs.sample.jsonl

## Professional Local + GitHub Setup

If you are starting from scratch and want the same workflow used in teams:

```powershell
pwsh ./scripts/pro_bootstrap.ps1 -RepoUrl https://github.com/muhnehh/moss-edge-docs-agent.git -LocalPath . -Branch main
```

This script will:

- clone when directory is empty
- initialize/connect `origin` when directory already has files
- fetch `origin`
- switch/create your target branch
- set upstream when remote branch exists

## Repository Layout

- moss_integration: scraping and Moss SDK retrieval wrappers
- reranker: ONNX export and runtime reranking
- agent: interactive chat pipeline
- metrics: benchmark harness and JSON output
- scripts: git and developer workflow scripts

Key files:

- reranker/train_reranker.py: fine-tuning pipeline
- reranker/export_to_onnx.py: ONNX + quantization pipeline
- agent/chat_agent.py: retrieval + rerank + routing
- agent/voice_agent.py: file-based STT -> answer -> optional TTS
- metrics/benchmark.py: latency benchmark report generator
- notebooks/explore_reranker.ipynb: reranker experiments in notebook format
- notebooks/explore_reranker.py: local reranker behavior exploration script

## CI Quality Gate

GitHub Actions workflow is included at `.github/workflows/ci.yml`.

- runs on push and pull request to main
- installs dependencies
- validates Python syntax for all project modules
- runs import smoke tests for core packages

## Advanced Interview Angle

To make this internship-grade, measure and report:

- median and p95 retrieval latency
- median and p95 reranker latency
- local answer rate (percentage of queries resolved without cloud fallback)
- quality checks for retrieved + reranked context

## Pro Git Workflow (Approval-Gated Push)

Use this script for a pro sync cycle. It can stage all files, commit, optionally pull with rebase, and push only when you approve.

```powershell
pwsh ./scripts/approve_push.ps1
```

Useful options:

```powershell
pwsh ./scripts/approve_push.ps1 -CommitMessage "feat: improve reranker routing"
pwsh ./scripts/approve_push.ps1 -SkipPull
```

This keeps control in your hands while making shipping fast and repeatable.
