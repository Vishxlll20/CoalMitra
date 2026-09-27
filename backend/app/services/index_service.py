"""Vector index (ChromaDB) with graceful demo fallback.

Real path (DEMO_MODE=0, deps installed): chromadb client with fastembed local
embeddings (multilingual-e5-small — works offline and handles Hindi).
Demo path: deterministic keyword-scoring retrieval over seeded text so the
Chat + Insights features work with zero ML deps. Identical interface.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from app.core.config import settings

_COLLECTION = None
_EMBEDDING = None


def _client():
    global _COLLECTION
    if _COLLECTION is None:
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            Path(settings.chroma_dir).mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(
                path=settings.chroma_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            _COLLECTION = client.get_or_create_collection("coalmitra")
        except Exception:
            _COLLECTION = False  # degraded: no real chroma
    return _COLLECTION


def _embed(texts: list[str]) -> list[list[float]]:
    """Embed texts with fastembed; fallback to a deterministic hash embedding."""
    global _EMBEDDING
    try:
        if _EMBEDDING is None:
            from fastembed import TextEmbedding
            _EMBEDDING = TextEmbedding(model_name=settings.embedding_model)
        return list(_EMBEDDING.embed(texts))
    except Exception:
        # deterministic SVD-ish fallback from chars (stable across runs)
        return [_hash_embed(t) for t in texts]


def _hash_embed(text: str, dim: int = 64) -> list[float]:
    vec = [0.0] * dim
    for tok in re.findall(r"[\wऀ-ॿ]+", text.lower()):
        for i in range(3):
            d = int(hashlib.md5(f"{tok}:{i}".encode()).hexdigest(), 16) % dim
            vec[d] += 1.0
    norm = sum(x * x for x in vec) ** 0.5 or 1
    return [x / norm for x in vec]


class Collection:
    """Minimal wrapper so demo/keyword and chroma paths share one API."""

    def __init__(self, real_collection):
        self._real = real_collection  # False or chroma collection

    def upsert(self, ids, documents, metadatas):
        if not self._real:
            return
        try:
            self._real.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=None,  # chroma computes via default ef if configured
            )
        except Exception:
            pass

    def query(self, query_texts, n_results=5, where=None):
        if not self._real:
            raise RuntimeError("chroma unavailable")
        return self._real.query(
            query_texts=query_texts,
            n_results=n_results,
            where=where,
        )

    def count(self):
        if not self._real:
            return 0
        try:
            return self._real.count()
        except Exception:
            return 0


def get_collection() -> Collection:
    return Collection(_client())


def keyword_search(question: str, docs_text: list[dict], top_k: int = 5) -> list[dict]:
    """Deterministic BM25-ish retrieval over seeded document chunks.

    docs_text: list of {document_id, title, page_number, bbox, char_start,
    char_end, text}. Used when no real chroma/embedding path is available.
    """
    toks = re.findall(r"[\wऀ-ॿ]+", question.lower())
    toks = [t for t in toks if len(t) > 1]
    if not toks:
        return []
    scored = []
    for d in docs_text:
        hay = d["text"].lower()
        score = sum(hay.count(t) for t in toks)
        # boost docs with exact title/block matches
        title_toks = re.findall(r"[\wऀ-ॿ]+", d.get("title", "").lower())
        boost = sum(2 for t in toks if t in title_toks)
        if score:
            scored.append((score + boost, d))
    scored.sort(key=lambda x: -x[0])
    return [d for _, d in scored[:top_k]]


def normalize_metadata(hit) -> dict:
    """Extract (document_id, page, bbox, snippet) from a chroma result doc."""
    meta = hit.get("metadata", {})
    doc = hit.get("document", "")
    return {
        "document_id": meta.get("document_id", ""),
        "page_number": int(meta.get("page_number", 1)),
        "source": doc[:400],
        "score": float(hit.get("distance", 0) or 0),
        "bbox": meta.get("bbox") or None,
        "char_start": int(meta.get("char_start", 0)),
        "char_end": int(meta.get("char_end", 100)),
        "title": meta.get("title", ""),
    }