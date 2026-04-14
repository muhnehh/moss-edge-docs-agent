# Moss Edge ONNX Reranker Model Card

## Summary

This reranker is a cross-encoder model used to reorder retrieved Moss documentation chunks before routing/answer generation.

- Base model: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- Fine-tuned model path: `reranker/models/reranker_finetuned`
- Quantized ONNX path: `reranker/models/reranker_onnx_finetuned_quantized`

## Training Data

- Source file: `data/train_pairs.sample.jsonl`
- Format: JSONL rows with `query`, `positive` or `positives`, and `negatives`
- Current sample size: 5 queries, 15 labeled pairs after expansion

This is a small seed dataset intended for pipeline validation and early benchmarking, not final production tuning.

## Training Configuration

Command used:

```bash
python -m reranker.train_reranker --data-path data/train_pairs.sample.jsonl --epochs 1 --batch-size 2 --eval-ratio 0.4 --output-dir reranker/models/reranker_finetuned
```

Key settings:

- Epochs: 1
- Batch size: 2
- Eval ratio: 0.4
- Max length: 512

## Export Configuration

Command used:

```bash
python -m reranker.export_to_onnx --source-model reranker/models/reranker_finetuned --raw-dir reranker/models/reranker_onnx_finetuned --quant-dir reranker/models/reranker_onnx_finetuned_quantized
```

- ONNX Runtime quantization preset: AVX2 INT8 dynamic

## Evaluation

Evaluation report file:

- `metrics/results/reranker_eval.json`

Command used:

```bash
python -m metrics.reranker_eval --data-path data/train_pairs.sample.jsonl --baseline-model cross-encoder/ms-marco-MiniLM-L-6-v2 --candidate-model reranker/models/reranker_finetuned --output metrics/results/reranker_eval.json
```

Measured results on the sample dataset (2026-04-14):

- Baseline top-1 accuracy: 0.80
- Fine-tuned top-1 accuracy: 0.80
- Top-1 delta: +0.00
- Avg margin delta: +0.1695
- Avg latency delta: -2.61 ms

## Latency Snapshot

Local rerank benchmark file:

- `metrics/results/benchmark_local.json`

Measured local rerank latency:

- Median rerank: 26.39 ms
- P95 rerank: 31.34 ms

## Limitations

- Current training corpus is very small and handcrafted.
- Metrics are from a seed dataset and should not be treated as final production quality.
- For interview-grade claims, re-run evaluation on a larger Moss-docs held-out set and report additional ranking metrics (for example: MRR@10, NDCG@10, Recall@k).