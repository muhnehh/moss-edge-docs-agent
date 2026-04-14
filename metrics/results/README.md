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

- retrieval median: 0.13 ms
- retrieval p95: 0.16 ms
- rerank median: 28.74 ms
- rerank p95: 35.64 ms
- total median: 28.88 ms
- total p95: 35.80 ms

Latest Moss-backed benchmark snapshot (2026-04-14):

- retrieval median: 5.58 ms
- retrieval p95: 6.47 ms
- rerank median: 15.75 ms
- rerank p95: 17.90 ms
- total median: 21.47 ms
- total p95: 23.96 ms
- note: first-query cold start observed around 2.8s

Latest reranker eval snapshot (2026-04-14):

- baseline top1 accuracy: 0.80
- fine-tuned top1 accuracy: 0.80
- margin delta: +0.1695
- avg latency delta: -2.61 ms
