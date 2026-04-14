from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import numpy as np
from optimum.onnxruntime import ORTModelForSequenceClassification
from transformers import AutoTokenizer


class ONNXReranker:
    def __init__(
        self,
        model_dir: str | None = None,
        max_input_chars: int | None = None,
        max_length: int | None = None,
    ) -> None:
        path = self._resolve_model_dir(model_dir)
        if not path.exists():
            raise RuntimeError(
                "Reranker model directory not found. Run: python -m reranker.export_to_onnx"
            )

        self.max_input_chars = (
            int(os.getenv("RERANK_INPUT_MAX_CHARS", "160"))
            if max_input_chars is None
            else max_input_chars
        )
        self.max_length = (
            int(os.getenv("RERANK_MAX_LENGTH", "192")) if max_length is None else max_length
        )

        model_file = None
        if (path / "model_quantized.onnx").exists():
            model_file = "model_quantized.onnx"
        elif (path / "model.onnx").exists():
            model_file = "model.onnx"

        if model_file:
            self.model = ORTModelForSequenceClassification.from_pretrained(
                path,
                file_name=model_file,
            )
        else:
            self.model = ORTModelForSequenceClassification.from_pretrained(path)
        self.tokenizer = AutoTokenizer.from_pretrained(path)

    @staticmethod
    def _resolve_model_dir(model_dir: str | None) -> Path:
        env_dir = os.getenv("RERANK_MODEL_DIR")
        if model_dir:
            return Path(model_dir)
        if env_dir:
            return Path(env_dir)

        candidates = [
            Path("reranker/models/reranker_onnx_finetuned_quantized"),
            Path("reranker/models/reranker_onnx_quantized"),
            Path("reranker/models/reranker_onnx_finetuned"),
            Path("reranker/models/reranker_onnx"),
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[0]

    def rerank(
        self, query: str, docs: list[dict[str, Any]], top_k: int = 3
    ) -> tuple[list[dict[str, Any]], float]:
        if not docs:
            return [], 0.0

        pairs: list[tuple[str, str]] = []
        for doc in docs:
            text = (doc.get("text") or "").strip()
            if self.max_input_chars > 0:
                text = text[: self.max_input_chars]
            pairs.append((query, text))

        t0 = time.perf_counter()

        inputs = self.tokenizer(
            pairs,
            padding=True,
            truncation=True,
            max_length=self.max_length,
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
