"""Quick exploration script for reranker behavior and latency.

Run:
    .\\.venv\\Scripts\\python.exe notebooks/explore_reranker.py
"""

import json
from pathlib import Path

from reranker.inference import ONNXReranker

SAMPLE_QUERY = "How do I create an index in Moss?"
SAMPLE_DOC_COUNT = 6


def load_docs(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise RuntimeError("Expected a list of corpus documents.")
    return payload


def main() -> None:
    corpus_path = Path("data/corpus.json")
    if not corpus_path.exists():
        raise FileNotFoundError("Missing data/corpus.json. Run moss_indexer first.")

    docs = load_docs(corpus_path)[:SAMPLE_DOC_COUNT]
    reranker = ONNXReranker()

    ranked, latency_ms = reranker.rerank(SAMPLE_QUERY, docs, top_k=3)

    print(f"Query: {SAMPLE_QUERY}")
    print(f"Rerank latency: {latency_ms:.2f}ms")
    print("Top docs:\n")

    for i, doc in enumerate(ranked, start=1):
        score = doc.get("rerank_score", 0.0)
        snippet = (doc.get("text") or "")[:180]
        print(f"{i}. id={doc.get('id')} score={score:.4f}")
        print(f"   {snippet}...")


if __name__ == "__main__":
    main()
