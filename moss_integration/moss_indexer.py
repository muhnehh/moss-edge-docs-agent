import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from inferedge_moss import DocumentInfo, MossClient

load_dotenv()

DOCS_URLS = [
    "https://docs.moss.dev/docs/start/what-is-moss",
    "https://docs.moss.dev/docs/start/quickstart",
    "https://docs.moss.dev/docs/start/core-concepts",
    "https://docs.moss.dev/docs/integrate/indexing-data",
    "https://docs.moss.dev/docs/integrate/retrieval",
    "https://docs.moss.dev/docs/integrate/authentication",
    "https://docs.moss.dev/docs/build/voice-agent-livekit",
    "https://docs.moss.dev/docs/build/offline-first-search",
]


@dataclass
class ChunkConfig:
    max_chars: int = 450
    min_chars: int = 70


def chunk_text(text: str, cfg: ChunkConfig) -> list[str]:
    sentences = [s.strip() for s in text.replace("\n", " ").split(". ") if s.strip()]
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        candidate = f"{current}{sentence}. "
        if len(candidate) > cfg.max_chars and current:
            chunks.append(current.strip())
            current = f"{sentence}. "
        else:
            current = candidate

    if current:
        chunks.append(current.strip())

    return [chunk for chunk in chunks if len(chunk) >= cfg.min_chars]


async def scrape_page(url: str, cfg: ChunkConfig) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup.select("nav, header, footer, script, style"):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    chunks = chunk_text(text, cfg)

    return [
        {
            "id": f"{url.rstrip('/').split('/')[-1]}-{i}",
            "text": chunk,
            "metadata": {"source_url": url, "chunk_index": str(i)},
        }
        for i, chunk in enumerate(chunks)
    ]


async def build_index() -> None:
    project_id = os.getenv("MOSS_PROJECT_ID")
    project_key = os.getenv("MOSS_PROJECT_KEY")
    index_name = os.getenv("MOSS_INDEX_NAME", "moss-docs")

    if not project_id or not project_key:
        raise RuntimeError("Missing MOSS_PROJECT_ID or MOSS_PROJECT_KEY in environment.")

    client = MossClient(project_id=project_id, project_key=project_key)

    cfg = ChunkConfig()
    all_docs: list[dict[str, Any]] = []

    for url in DOCS_URLS:
        docs = await scrape_page(url, cfg)
        all_docs.extend(docs)
        print(f"Scraped {len(docs)} chunks from {url}")

    moss_docs = [
        DocumentInfo(doc["id"], doc["text"], doc.get("metadata"))
        for doc in all_docs
    ]

    print(f"Total chunks: {len(all_docs)}")
    await client.create_index(index_name, moss_docs, model_id="moss-minilm")
    print(f"Index created: {index_name}")

    out = Path("data") / "corpus.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(all_docs, indent=2), encoding="utf-8")
    print(f"Saved corpus snapshot to {out}")


if __name__ == "__main__":
    asyncio.run(build_index())
