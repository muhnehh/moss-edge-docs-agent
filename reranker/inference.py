from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import numpy as np
from optimum.onnxruntime import ORTModelForSequenceClassification
from transformers import AutoTokenizer


class ONNXReranker:
    def __init__(self, model_dir: str = "reranker/models/reranker_onnx_quantized") -> None:
        path = Path(model_dir)
        if not path.exists():
            raise RuntimeError(
                "Reranker model directory not found. Run: python -m reranker.export_to_onnx"
            )

        self.model = ORTModelForSequenceClassification.from_pretrained(path)
        self.tokenizer = AutoTokenizer.from_pretrained(path)

    def rerank(
        self, query: str, docs: list[dict[str, Any]], top_k: int = 3
    ) -> tuple[list[dict[str, Any]], float]:
        if not docs:
            return [], 0.0

        pairs = [(query, (doc.get("text") or "").strip()) for doc in docs]
        t0 = time.perf_counter()

        inputs = self.tokenizer(
            pairs,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )

        outputs = self.model(**inputs)
        logits = outputs.logits.squeeze(-1)
        scores = logits.detach().cpu().numpy() if hasattr(logits, "detach") else np.array(logits)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        ranked: list[tuple[dict[str, Any], float]] = sorted(
            [(doc, float(score)) for doc, score in zip(docs, scores, strict=False)],
            key=lambda item: item[1],
            reverse=True,
        )

        top_docs: list[dict[str, Any]] = []
        for doc, score in ranked[:top_k]:
            enriched = dict(doc)
            enriched["rerank_score"] = score
            top_docs.append(enriched)

        return top_docs, elapsed_ms

    @staticmethod
    def should_use_cloud_llm(top_score: float, threshold: float = 0.3) -> bool:
        return top_score < threshold
