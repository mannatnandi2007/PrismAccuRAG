"""Lightweight query-type classifier (factoid vs multi-hop).

Uses a combination of:
1. Cosine similarity to prototype queries
2. Heuristic signals (question words, entity count, clause markers)
"""

from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings

# Prototype queries for each type
FACTOID_PROTOTYPES = [
    "What is the capital of France?",
    "Who invented the telephone?",
    "When was the Declaration of Independence signed?",
    "What is the boiling point of water?",
    "How tall is Mount Everest?",
    "What year did World War II end?",
    "Who is the CEO of Tesla?",
    "What is the chemical formula for water?",
]

MULTIHOP_PROTOTYPES = [
    "How did the economic policies of the 1980s affect income inequality in the following decades?",
    "Compare and contrast the causes of World War I and World War II.",
    "What were the long-term consequences of the Industrial Revolution on urban planning?",
    "Explain how climate change affects both marine ecosystems and agricultural productivity.",
    "How do trade agreements between countries influence domestic employment rates?",
    "What is the relationship between social media usage and mental health outcomes in teenagers?",
    "Trace the evolution of democratic governance from ancient Athens to modern representative democracy.",
    "How did advances in computing influence both cryptography and privacy legislation?",
]

# Heuristic signals
FACTOID_WORDS = {"what", "who", "when", "where", "which", "name", "define"}
MULTIHOP_MARKERS = {"compare", "contrast", "relationship", "influence", "affect",
                    "how did", "explain how", "trace", "evolution", "consequences",
                    "and", "both", "between"}

_proto_embeddings: dict | None = None


def _get_prototype_embeddings(model: SentenceTransformer) -> dict:
    global _proto_embeddings
    if _proto_embeddings is None:
        f_emb = model.encode(FACTOID_PROTOTYPES, convert_to_numpy=True)
        m_emb = model.encode(MULTIHOP_PROTOTYPES, convert_to_numpy=True)
        # Normalise
        f_emb = f_emb / np.linalg.norm(f_emb, axis=1, keepdims=True)
        m_emb = m_emb / np.linalg.norm(m_emb, axis=1, keepdims=True)
        _proto_embeddings = {"factoid": f_emb, "multi-hop": m_emb}
    return _proto_embeddings


def classify_query(
    query: str,
    model: SentenceTransformer,
) -> tuple[str, float]:
    """Classify query as 'factoid' or 'multi-hop'.

    Returns (query_type, budget_ratio).
    """
    protos = _get_prototype_embeddings(model)

    # Embed query
    q_emb = model.encode([query], convert_to_numpy=True)
    q_emb = q_emb / np.linalg.norm(q_emb, axis=1, keepdims=True)

    # Cosine similarity to prototypes (mean of top-3)
    factoid_sims = (q_emb @ protos["factoid"].T).flatten()
    multihop_sims = (q_emb @ protos["multi-hop"].T).flatten()

    factoid_score = float(np.sort(factoid_sims)[-3:].mean())
    multihop_score = float(np.sort(multihop_sims)[-3:].mean())

    # Heuristic adjustments
    query_lower = query.lower()
    words = set(query_lower.split())

    # Boost factoid if starts with a simple question word and is short
    if words & FACTOID_WORDS and len(query.split()) < 12:
        factoid_score += 0.1

    # Boost multi-hop if contains comparison/relationship markers
    if any(marker in query_lower for marker in MULTIHOP_MARKERS):
        multihop_score += 0.1

    # Decide
    if multihop_score > factoid_score:
        return "multi-hop", settings.multihop_budget
    else:
        return "factoid", settings.factoid_budget
