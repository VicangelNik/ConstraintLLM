from __future__ import annotations

from typing import Optional

import requests


def rerank_documents(query: str, documents: list[str], endpoint: Optional[str] = None, topk: int = 4) -> list[str]:
    """Optional remote reranking endpoint that falls back to the first top-k documents."""
    if not endpoint:
        return documents[:topk]

    response = requests.post(
        endpoint,
        json={"query": query, "documents": documents},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    results = payload.get("results", [])
    reranked = []
    for item in results[:topk]:
        document = item.get("document")
        if isinstance(document, dict):
            reranked.append(document.get("text", ""))
        elif isinstance(document, str):
            reranked.append(document)
    return reranked
