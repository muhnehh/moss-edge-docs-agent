import asyncio
import os
import time
from typing import Any

from dotenv import load_dotenv
from openai import AsyncOpenAI

from moss_integration.moss_retriever import MossRetriever
from reranker.inference import ONNXReranker

load_dotenv()


class MossEdgeAgent:
    def __init__(self) -> None:
        self.retrieve_top_k = self._read_int_env("MOSS_RETRIEVE_TOP_K", default=3, minimum=1)
        self.rerank_top_k = self._read_int_env("RERANK_TOP_K", default=3, minimum=1)

        self.retriever = MossRetriever(top_k=self.retrieve_top_k)
        self.reranker = ONNXReranker()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai = AsyncOpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
        self.rerank_threshold = float(os.getenv("RERANK_THRESHOLD", "0.3"))

    @staticmethod
    def _read_int_env(name: str, default: int, minimum: int = 1) -> int:
        raw = os.getenv(name)
        if raw is None:
            return default
        try:
            value = int(raw)
        except ValueError:
            return default
        return max(minimum, value)

    async def answer(self, question: str) -> dict[str, Any]:
        timings: dict[str, float | str] = {}

        t_retrieve = time.perf_counter()
        candidates = await self.retriever.retrieve(question)
        timings["moss_retrieval_ms"] = (time.perf_counter() - t_retrieve) * 1000

        top_docs, rerank_ms = self.reranker.rerank(question, candidates, top_k=self.rerank_top_k)
        timings["rerank_ms"] = rerank_ms

        top_score = top_docs[0].get("rerank_score", 0.0) if top_docs else 0.0
        use_cloud = self.reranker.should_use_cloud_llm(
            float(top_score),
            threshold=self.rerank_threshold,
        )
        can_use_cloud = use_cloud and self.openai is not None
        timings["path"] = "cloud" if can_use_cloud else "local"

        if can_use_cloud:
            t_cloud = time.perf_counter()
            answer = await self._cloud_answer(question, top_docs)
            timings["cloud_llm_ms"] = (time.perf_counter() - t_cloud) * 1000
            timings["answer_source"] = "cloud_fallback"
        else:
            answer = self._extract_local_answer(top_docs)
            timings["answer_source"] = "local_extraction"
            if use_cloud and self.openai is None:
                timings["fallback_reason"] = "missing_openai_api_key"

        timings["total_ms"] = sum(v for k, v in timings.items() if k.endswith("_ms"))

        return {
            "answer": answer,
            "sources": [doc.get("id", "unknown") for doc in top_docs],
            "timings": timings,
            "top_docs": top_docs,
        }

    @staticmethod
    def _extract_local_answer(docs: list[dict[str, Any]]) -> str:
        if not docs:
            return "I could not find relevant information in the indexed docs."
        top = docs[0]
        snippet = (top.get("text") or "").strip()
        return f"{snippet}\n\nSource: {top.get('id', 'unknown')}"

    async def _cloud_answer(self, question: str, docs: list[dict[str, Any]]) -> str:
        if self.openai is None:
            return "OpenAI fallback is not configured. Set OPENAI_API_KEY in your .env file."

        context = "\n\n".join((doc.get("text") or "") for doc in docs)
        response = await self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Answer only from the provided context. If unknown, say unknown.",
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {question}",
                },
            ],
            max_tokens=220,
            temperature=0.1,
        )
        content = response.choices[0].message.content
        return content or "No response returned."


async def main() -> None:
    agent = MossEdgeAgent()
    print("Moss Edge Agent ready. Type your question or 'exit'.")

    while True:
        question = input("\n> ").strip()
        if question.lower() in {"exit", "quit"}:
            break

        result = await agent.answer(question)
        print("\nAnswer:\n")
        print(result["answer"])
        print("\nTimings:")
        print(result["timings"])


if __name__ == "__main__":
    asyncio.run(main())
