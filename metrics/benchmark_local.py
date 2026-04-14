import argparse
import json
import re
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reranker.inference import ONNXReranker

TEST_QUESTIONS = [
    "How do I install the Moss SDK?",
    "What is the difference between moss-minilm and moss-mediumlm?",
    "How do I create an index in Moss?",
    "What retrieval latency does Moss target?",
    "Can Moss run offline?",
    "How do I authenticate with Moss API credentials?",
    "What query parameters does Moss query accept?",
    "How does Moss handle index updates?",
    "How does Moss compare to remote vector DB setups?",
    "How do I integrate Moss with a voice agent?",
]

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def percentile_p95(values: list[float]) -> float | None:
    if not values:
        return None
    idx = int(0.95 * (len(values) - 1))
    return sorted(values)[idx]


def tokenize(text: str) -> set[str]:
    return set(TOKEN_PATTERN.findall((text or "").lower()))


def load_docs_from_jsonl(path: Path) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []

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

            for idx, text in enumerate(positives):
                snippet = (text or "").strip()
                if snippet:
                    docs.append(
                        {
                            "id": f"pos-{line_no}-{idx}",
                            "text": snippet,
                            "label": "positive",
                            "query": query,
                        }
                    )

            for idx, text in enumerate(negatives):
                snippet = (text or "").strip()
                if snippet:
                    docs.append(
                        {
                            "id": f"neg-{line_no}-{idx}",
                            "text": snippet,
                            "label": "negative",
                            "query": query,
                        }
                    )

    if not docs:
        raise RuntimeError(f"No candidate docs found in dataset: {path}")

    return docs


def keyword_retrieve(query: str, docs: list[dict[str, Any]], top_k: int = 8) -> list[dict[str, Any]]:
    q_tokens = tokenize(query)
    scored: list[tuple[float, dict[str, Any]]] = []

    for doc in docs:
        d_tokens = tokenize(str(doc.get("text", "")))
        overlap = len(q_tokens & d_tokens)
        score = overlap / max(1, len(q_tokens))
        scored.append((score, doc))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in scored[:top_k]]


def run_benchmark(
    data_path: Path,
    model_dir: str,
    retrieve_top_k: int,
    rerank_top_k: int,
) -> dict[str, Any]:
    docs = load_docs_from_jsonl(data_path)
    reranker = ONNXReranker(model_dir=model_dir)
    samples: list[dict[str, Any]] = []

    for question in TEST_QUESTIONS:
        t_retrieve = time.perf_counter()
        candidates = keyword_retrieve(question, docs, top_k=retrieve_top_k)
        retrieval_ms = (time.perf_counter() - t_retrieve) * 1000

        _, rerank_ms = reranker.rerank(question, candidates, top_k=rerank_top_k)
        total_ms = retrieval_ms + rerank_ms

        samples.append(
            {
                "question": question,
                "retrieval_ms": retrieval_ms,
                "rerank_ms": rerank_ms,
                "total_ms": total_ms,
                "path": "local",
            }
        )
        print(f"{question[:48]:48} | total={total_ms:.2f}ms")

    retrieval = [float(s["retrieval_ms"]) for s in samples]
    rerank = [float(s["rerank_ms"]) for s in samples]
    total = [float(s["total_ms"]) for s in samples]

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "local-keyword-plus-onnx",
        "dataset": str(data_path),
        "n_questions": len(samples),
        "retrieval": {
            "median_ms": statistics.median(retrieval) if retrieval else None,
            "p95_ms": percentile_p95(retrieval),
        },
        "onnx_rerank": {
            "median_ms": statistics.median(rerank) if rerank else None,
            "p95_ms": percentile_p95(rerank),
        },
        "total_fast_path": {
            "median_ms": statistics.median(total) if total else None,
            "p95_ms": percentile_p95(total),
        },
        "samples": samples,
    }

    out = Path("metrics/results/benchmark_local.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nSaved benchmark report to: {out}")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local latency benchmark without Moss credentials.")
    parser.add_argument(
        "--data-path",
        default="data/train_pairs.sample.jsonl",
        help="JSONL dataset used to create local retrieval candidates.",
    )
    parser.add_argument(
        "--model-dir",
        default="reranker/models/reranker_onnx_quantized",
        help="Directory containing quantized ONNX reranker model.",
    )
    parser.add_argument("--retrieve-top-k", type=int, default=8)
    parser.add_argument("--rerank-top-k", type=int, default=3)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_benchmark(
        data_path=Path(args.data_path),
        model_dir=args.model_dir,
        retrieve_top_k=args.retrieve_top_k,
        rerank_top_k=args.rerank_top_k,
    )