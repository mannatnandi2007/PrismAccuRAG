"""Document chunking, embedding, and FAISS indexing."""

from __future__ import annotations

import re
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from app.config import settings


def _simple_token_split(text: str) -> list[str]:
    """Rough whitespace-based tokeniser (good enough for chunking budgets)."""
    return text.split()


def chunk_documents(
    texts: list[str],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[dict]:
    """Split documents into overlapping token-level chunks.

    Returns list of dicts: {"text": str, "doc_idx": int, "chunk_idx": int, "token_count": int}
    """
    chunk_size = chunk_size or settings.chunk_size
    overlap = overlap or settings.chunk_overlap

    chunks: list[dict] = []
    global_idx = 0

    for doc_idx, text in enumerate(texts):
        # Normalise whitespace
        text = re.sub(r"\s+", " ", text).strip()
        tokens = _simple_token_split(text)
        start = 0
        while start < len(tokens):
            end = min(start + chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = " ".join(chunk_tokens)
            chunks.append({
                "text": chunk_text,
                "doc_idx": doc_idx,
                "chunk_idx": global_idx,
                "token_count": len(chunk_tokens),
            })
            global_idx += 1
            if end >= len(tokens):
                break
            start += chunk_size - overlap

    return chunks


def embed_chunks(chunks: list[dict], model: SentenceTransformer) -> np.ndarray:
    """Embed chunk texts and L2-normalise for cosine similarity via inner product."""
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    # Normalise so inner-product == cosine similarity
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    embeddings = embeddings / norms
    return embeddings.astype("float32")


def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatIP:
    """Build an in-memory FAISS inner-product index."""
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    return index
