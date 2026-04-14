This directory stores generated benchmark and evaluation reports.

Generated JSON outputs are ignored by git (`metrics/results/*.json`) to avoid committing machine-specific runs.

Commands:

- Moss-backed benchmark (requires Moss credentials):
	- `python -m metrics.benchmark`
- Local benchmark (no Moss credentials required):
	- `python -m metrics.benchmark_local --data-path data/train_pairs.sample.jsonl --model-dir reranker/models/reranker_onnx_finetuned_quantized`
- Baseline vs fine-tuned reranker eval:
	- `python -m metrics.reranker_eval --data-path data/train_pairs.sample.jsonl --baseline-model cross-encoder/ms-marco-MiniLM-L-6-v2 --candidate-model reranker/models/reranker_finetuned --output metrics/results/reranker_eval.json`

Latest local benchmark snapshot (2026-04-14):

- retrieval median: 0.11 ms
- rerank median: 26.39 ms
- total median: 26.48 ms

Latest Moss-backed benchmark snapshot (2026-04-14):

- retrieval median: 5.17 ms
- retrieval p95: 5.79 ms
- rerank median: 177.40 ms
- rerank p95: 246.43 ms
- total median: 182.32 ms
- total p95: 277.30 ms
- note: first-query cold start observed around 3.0s

Latest reranker eval snapshot (2026-04-14):

- baseline top1 accuracy: 0.80
- fine-tuned top1 accuracy: 0.80
- margin delta: +0.1695
- avg latency delta: -2.61 ms
