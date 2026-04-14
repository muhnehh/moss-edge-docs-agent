import os
from typing import Any

from dotenv import load_dotenv
from inferedge_moss import MossClient, QueryOptions

load_dotenv()


class MossRetriever:
    def __init__(self, index_name: str | None = None, top_k: int = 8) -> None:
        project_id = os.getenv("MOSS_PROJECT_ID")
        project_key = os.getenv("MOSS_PROJECT_KEY")
        if not project_id or not project_key:
            raise RuntimeError("Missing MOSS_PROJECT_ID or MOSS_PROJECT_KEY in environment.")

        self.client = MossClient(project_id=project_id, project_key=project_key)
        self.index_name = index_name or os.getenv("MOSS_INDEX_NAME", "moss-docs")
        self.top_k = top_k
        self._loaded = False

    async def ensure_loaded(self) -> None:
        if self._loaded:
            return
        await self.client.load_index(self.index_name)
        self._loaded = True

    async def retrieve(self, query: str, top_k: int | None = None) -> list[dict[str, Any]]:
        await self.ensure_loaded()
        response = await self.client.query(
            self.index_name,
            query,
            QueryOptions(top_k=top_k or self.top_k),
        )

        docs = getattr(response, "docs", None)
        if docs is None and isinstance(response, dict):
            docs = response.get("docs", [])

        normalized: list[dict[str, Any]] = []
        for doc in docs or []:
            if isinstance(doc, dict):
                normalized.append(doc)
                continue

            normalized.append(
                {
                    "id": getattr(doc, "id", "unknown"),
                    "text": getattr(doc, "text", ""),
                    "metadata": getattr(doc, "metadata", None),
                    "score": getattr(doc, "score", None),
                }
            )

        return normalized
