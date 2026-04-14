import asyncio
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

from agent.chat_agent import MossEdgeAgent

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


def percentile_p95(values: list[float]) -> float | None:
    if not values:
        return None
    idx = int(0.95 * (len(values) - 1))
    return sorted(values)[idx]


async def run_benchmark() -> dict:
    agent = MossEdgeAgent()
    samples: list[dict] = []

    for question in TEST_QUESTIONS:
        result = await agent.answer(question)
        timings = result["timings"]
        samples.append({"question": question, **timings})
        print(
            f"{question[:48]:48} | total={timings['total_ms']:.1f}ms | path={timings['path']}"
        )

    retrieval = [float(s["moss_retrieval_ms"]) for s in samples]
    rerank = [float(s["rerank_ms"]) for s in samples]
    local = [float(s["total_ms"]) for s in samples if s["path"] == "local"]

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "n_questions": len(samples),
        "pct_answered_locally": (len(local) / len(samples) * 100) if samples else 0,
        "moss_retrieval": {
            "median_ms": statistics.median(retrieval) if retrieval else None,
            "p95_ms": percentile_p95(retrieval),
        },
        "onnx_rerank": {
            "median_ms": statistics.median(rerank) if rerank else None,
            "p95_ms": percentile_p95(rerank),
        },
        "total_fast_path": {
            "median_ms": statistics.median(local) if local else None,
            "p95_ms": percentile_p95(local),
        },
        "samples": samples,
    }

    out = Path("metrics/results/benchmark.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nSaved benchmark report to: {out}")
    return report


if __name__ == "__main__":
    asyncio.run(run_benchmark())
