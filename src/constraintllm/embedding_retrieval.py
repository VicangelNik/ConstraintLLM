from __future__ import annotations

import math
import time
from typing import Iterable

from openai import APITimeoutError, APIConnectionError, InternalServerError, OpenAI

from .config import Settings


def _dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _norm(vector: list[float]) -> float:
    return math.sqrt(sum(value * value for value in vector))


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    left_norm = _norm(left)
    right_norm = _norm(right)
    if left_norm == 0 or right_norm == 0:
        return -1.0
    return _dot(left, right) / (left_norm * right_norm)


class EmbeddingRetriever:
    """使用 OpenAI 兼容 embedding 接口进行检索。"""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = OpenAI(
            api_key=settings.embedding_api_key,
            base_url=settings.embedding_api_base,
            timeout=settings.request_timeout,
        )
        self._documents: list[dict] = []
        self._document_vectors: list[list[float]] = []

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        """调用 embedding 接口并带有限重试。"""
        last_error: Exception | None = None
        for attempt in range(self.settings.request_retries + 1):
            try:
                response = self.client.embeddings.create(
                    model=self.settings.embedding_model,
                    input=texts,
                )
                return [list(item.embedding) for item in response.data]
            except (APITimeoutError, APIConnectionError, InternalServerError) as exc:
                last_error = exc
                if attempt >= self.settings.request_retries:
                    break
                time.sleep(max(1, self.settings.request_retry_backoff) * (attempt + 1))
        if last_error is not None:
            raise last_error
        return []

    def build_index(self, documents: Iterable[dict]) -> None:
        """预计算语料 embedding，避免每个查询重复编码。"""
        self._documents = list(documents)
        texts = [str(document.get("problem", "")).strip() for document in self._documents]
        self._document_vectors = []
        batch_size = max(1, self.settings.embedding_batch_size)
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            self._document_vectors.extend(self._embed_batch(batch))

    def topk(self, query: str, topk: int) -> list[dict]:
        """返回与 query embedding 最相近的 top-k 样本。"""
        if not self._documents or not self._document_vectors:
            return []
        query_vector = self._embed_batch([query])[0]
        scored: list[tuple[float, dict]] = []
        for document, vector in zip(self._documents, self._document_vectors):
            scored.append((_cosine_similarity(query_vector, vector), document))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in scored[:topk]]
