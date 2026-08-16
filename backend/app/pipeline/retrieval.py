"""Top-k retrieval via FAISS cosine similarity."""

from __future__ import annotations

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from app.config import settings


def retrieve(
    query: str,
    index: faiss.IndexFlatIP,
    chunks: list[dict],
    model: SentenceTransformer,
    top_k: int | None = None,
) -> list[dict]:
    """Return top-k chunks ranked by cosine similarity to the query.

    Each returned dict has the original chunk fields plus 'score'.
    """
    top_k = min(top_k or settings.top_k, len(chunks))

    # Embed & normalise query
    q_emb = model.encode([query], show_progress_bar=False, convert_to_numpy=True)
    q_emb = q_emb / np.linalg.norm(q_emb, axis=1, keepdims=True)
    q_emb = q_emb.astype("float32")

    scores, indices = index.search(q_emb, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue  # FAISS returns -1 for missing
        chunk = dict(chunks[idx])
        chunk["score"] = float(score)
        results.append(chunk)

    return results
