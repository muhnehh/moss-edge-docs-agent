import argparse
import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sentence_transformers import CrossEncoder


def percentile_p95(values: list[float]) -> float | None:
    if not values:
        return None
    idx = int(0.95 * (len(values) - 1))
    return sorted(values)[idx]


def parse_records(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line:
                continue

            row = json.loads(line)
            query = (row.get("query") or "").strip()
            positives = row.get("positive") or row.get("positives") or []
            negatives = row.get("negatives") or []

            if isinstance(positives, str):
                positives = [positives]
            if isinstance(negatives, str):
                negatives = [negatives]

            positives = [(text or "").strip() for text in positives if (text or "").strip()]
            negatives = [(text or "").strip() for text in negatives if (text or "").strip()]

            if not query or not positives or not negatives:
                raise ValueError(
                    f"Invalid row at line {line_no}: expected query + positives + negatives."
                )

            rows.append(
                {
                    "query": query,
                    "positives": positives,
                    "negatives": negatives,
                }
            )

    if not rows:
        raise RuntimeError(f"No evaluation records found in {path}")

    return rows


def evaluate_model(model_ref: str, rows: list[dict[str, Any]], max_length: int) -> dict[str, Any]:
    model = CrossEncoder(model_ref, max_length=max_length)

    n_rows = len(rows)
    hits = 0
    latencies: list[float] = []
    margins: list[float] = []
    per_query: list[dict[str, Any]] = []

    for row in rows:
        query = row["query"]
        positives = row["positives"]
        negatives = row["negatives"]
        candidates = positives + negatives
        labels = [1] * len(positives) + [0] * len(negatives)
        pairs = [(query, candidate) for candidate in candidates]

        t0 = time.perf_counter()
        scores = model.predict(pairs)
        latency_ms = (time.perf_counter() - t0) * 1000
        latencies.append(latency_ms)

        best_idx = max(range(len(scores)), key=lambda idx: float(scores[idx]))
        best_is_positive = labels[best_idx] == 1
        if best_is_positive:
            hits += 1

        pos_scores = [float(score) for score, label in zip(scores, labels, strict=False) if label == 1]
        neg_scores = [float(score) for score, label in zip(scores, labels, strict=False) if label == 0]
        margin = statistics.mean(pos_scores) - (max(neg_scores) if neg_scores else 0.0)
        margins.append(margin)

        per_query.append(
            {
                "query": query,
                "latency_ms": latency_ms,
                "top1_is_positive": best_is_positive,
                "margin": margin,
            }
        )

    return {
        "n_queries": n_rows,
        "top1_accuracy": hits / n_rows,
        "avg_latency_ms": statistics.mean(latencies) if latencies else None,
        "p95_latency_ms": percentile_p95(latencies),
        "avg_margin": statistics.mean(margins) if margins else None,
        "per_query": per_query,
    }


def run_eval(
    data_path: Path,
    baseline_model: str,
    candidate_model: str,
    max_length: int,
    output_path: Path,
) -> dict[str, Any]:
    rows = parse_records(data_path)
    baseline = evaluate_model(baseline_model, rows, max_length=max_length)
    candidate = evaluate_model(candidate_model, rows, max_length=max_length)

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": str(data_path),
        "baseline_model": baseline_model,
        "candidate_model": candidate_model,
        "baseline": baseline,
        "candidate": candidate,
        "delta": {
            "top1_accuracy": candidate["top1_accuracy"] - baseline["top1_accuracy"],
            "avg_margin": candidate["avg_margin"] - baseline["avg_margin"],
            "avg_latency_ms": candidate["avg_latency_ms"] - baseline["avg_latency_ms"],
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Baseline top1 accuracy: {baseline['top1_accuracy']:.3f}")
    print(f"Candidate top1 accuracy: {candidate['top1_accuracy']:.3f}")
    print(f"Delta top1 accuracy: {report['delta']['top1_accuracy']:+.3f}")
    print(f"Saved reranker eval report to: {output_path}")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare baseline and fine-tuned reranker quality.")
    parser.add_argument(
        "--data-path",
        default="data/train_pairs.sample.jsonl",
        help="JSONL dataset with query, positive(s), and negatives.",
    )
    parser.add_argument(
        "--baseline-model",
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        help="Baseline cross-encoder model id.",
    )
    parser.add_argument(
        "--candidate-model",
        default="reranker/models/reranker_finetuned",
        help="Candidate model path (usually your fine-tuned model).",
    )
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument(
        "--output",
        default="metrics/results/reranker_eval.json",
        help="Path to JSON report output.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_eval(
        data_path=Path(args.data_path),
        baseline_model=args.baseline_model,
        candidate_model=args.candidate_model,
        max_length=args.max_length,
        output_path=Path(args.output),
    )