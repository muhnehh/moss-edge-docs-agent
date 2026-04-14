# moss-edge-docs-agent

A production-style edge retrieval agent using Moss for retrieval and an ONNX reranker for local ranking and routing.

## Fork Disclosure

This repository is a fork of `usemoss/moss`. The fork status is intentional, and this repo includes both upstream content and my implementation work.

Upstream foundation I reused:

- Moss SDK usage patterns and multi-package ecosystem examples.
- Existing docs and release workflows from the upstream monorepo layout.

## What I Built on Top of Moss

What I added in this fork:

- A focused edge-agent pipeline in `agent/` with retrieval, reranking, routing, and optional voice flow.
- Moss integration layer in `moss_integration/` for indexing and retrieval wrappers.
- Reranker training/export/inference flow in `reranker/`.
- Benchmark and eval utilities in `metrics/`, including local latency benchmarking and baseline-vs-finetuned reranker evaluation.
- Project-specific scripts in `scripts/` and tests in `tests/` for this agent workflow.

## How to Get Moss Credentials and Run the Real Benchmark

1. In the Moss dashboard, open API Keys for your project.
2. Copy the environment-variable snippet from the Environment Variables box.
3. Create a local `.env` in the repo root and paste values for:
	- `MOSS_PROJECT_ID`
	- `MOSS_PROJECT_KEY`
	- `OPENAI_API_KEY` (needed for cloud fallback and voice path)
4. Ensure your project has an index (dashboard currently shows `0 / 3 indexes` in your screenshot), then run:
	- `python -m moss_integration.moss_indexer`
5. Run the Moss-backed benchmark:
	- `python -m metrics.benchmark`
6. Use the generated JSON at `metrics/results/benchmark.json` and paste the measured table into this README.

Security notes:

- Never commit `.env`.
- If you accidentally exposed a key, rotate it in the Moss dashboard immediately.

## Measured Evidence (Apr 14, 2026)

### 1) Latency Numbers (Real Moss-Backed Run Output)

I ran the Moss-backed benchmark on this machine after indexing docs with valid Moss credentials. To keep the run local-only (and avoid cloud fallback noise), I forced local routing for benchmark execution:

```powershell
$env:RERANK_THRESHOLD='-999'; python -m metrics.benchmark
```

Latest measured results from `metrics/results/benchmark.json`:

| Component | Median (ms) | P95 (ms) |
|---|---:|---:|
| Moss retrieval | 5.17 | 5.79 |
| ONNX rerank | 177.40 | 246.43 |
| Total fast path | 182.32 | 277.30 |

Sample terminal output from that run:

```text
How do I install the Moss SDK?                   | total=3017.7ms | path=local
What is the difference between moss-minilm and m | total=92.3ms   | path=local
How do I create an index in Moss?                | total=137.5ms  | path=local
...
Saved benchmark report to: metrics\results\benchmark.json
```

Cold-start note: the first query includes index/model warm-up and is much slower (~3.0s). Median and P95 values above are the reported aggregate metrics across all 10 benchmark questions.

Supplemental local-offline benchmark (no Moss network call) is also available in `metrics/results/benchmark_local.json`.

### 2) ONNX Reranker Fingerprint (Model + Training + Eval)

Base reranker model:

- `cross-encoder/ms-marco-MiniLM-L-6-v2`

Fine-tune command used:

```bash
python -m reranker.train_reranker --data-path data/train_pairs.sample.jsonl --epochs 1 --batch-size 2 --eval-ratio 0.4 --output-dir reranker/models/reranker_finetuned
```

Export + quantize command used:

```bash
python -m reranker.export_to_onnx --source-model reranker/models/reranker_finetuned --raw-dir reranker/models/reranker_onnx_finetuned --quant-dir reranker/models/reranker_onnx_finetuned_quantized
```

Baseline vs fine-tuned evaluation command:

```bash
python -m metrics.reranker_eval --data-path data/train_pairs.sample.jsonl --baseline-model cross-encoder/ms-marco-MiniLM-L-6-v2 --candidate-model reranker/models/reranker_finetuned --output metrics/results/reranker_eval.json
```

Evaluation summary (same sample dataset):

| Metric | Baseline | Fine-tuned | Delta |
|---|---:|---:|---:|
| Top-1 accuracy | 0.80 | 0.80 | +0.00 |
| Avg margin (positive vs hardest negative) | 5.1974 | 5.3669 | +0.1695 |
| Avg latency per query (ms) | 19.10 | 16.49 | -2.61 |
| P95 latency per query (ms) | 19.66 | 15.45 | -4.21 |

Interpretation: on this tiny sample set, accuracy is unchanged, while ranking margin and latency improved. This is honest early evidence, not a final quality claim.

Full reranker details are documented in `reranker/MODEL_CARD.md`.

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

- Local ONNX cross-encoder reranking for better precision and low-latency ranking.
- Query routing that avoids unnecessary cloud calls.
- Reproducible benchmark reporting with latency metrics and raw JSON outputs.
- Transparent reporting of measured numbers, including when results are above target.

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

7. Run local benchmark (no Moss credentials required):

```bash
python -m metrics.benchmark_local --data-path data/train_pairs.sample.jsonl --model-dir reranker/models/reranker_onnx_finetuned_quantized
```

8. Compare baseline vs fine-tuned reranker:

```bash
python -m metrics.reranker_eval --data-path data/train_pairs.sample.jsonl --baseline-model cross-encoder/ms-marco-MiniLM-L-6-v2 --candidate-model reranker/models/reranker_finetuned --output metrics/results/reranker_eval.json
```

9. Run tests:

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
