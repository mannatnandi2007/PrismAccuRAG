"""Graph-based pruning: remove low-value sentences to meet token budget."""

from __future__ import annotations

import numpy as np
import networkx as nx
from sentence_transformers import SentenceTransformer


def _score_nodes(
    G: nx.Graph,
    query: str,
    model: SentenceTransformer,
    sentences: list[dict],
) -> dict[int, float]:
    """Score each sentence node by:
    (a) query relevance (cosine similarity)  — weight 0.5
    (b) graph centrality (degree centrality)  — weight 0.3
    (c) information density (entities, numbers, citations) — weight 0.2
    """
    # (a) Query relevance via embedding similarity
    sent_texts = [s["text"] for s in sentences]
    all_texts = [query] + sent_texts
    embeddings = model.encode(all_texts, convert_to_numpy=True)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    embeddings = embeddings / norms

    q_emb = embeddings[0]
    sent_embs = embeddings[1:]

    relevance = sent_embs @ q_emb  # cosine similarities

    # (b) Graph centrality
    degree_centrality = nx.degree_centrality(G)

    # (c) Information density
    scores = {}
    for i, sent in enumerate(sentences):
        nid = sent["idx"]
        if nid not in G:
            continue

        node_data = G.nodes[nid]
        info_score = 0.0
        if node_data.get("has_numbers", False):
            info_score += 0.4
        if node_data.get("has_citations", False):
            info_score += 0.3
        entity_bonus = min(node_data.get("entity_count", 0) * 0.15, 0.6)
        info_score += entity_bonus

        # Combine
        scores[nid] = (
            0.5 * float(relevance[i])
            + 0.3 * degree_centrality.get(nid, 0.0)
            + 0.2 * info_score
        )

    return scores


def prune_graph(
    G: nx.Graph,
    sentences: list[dict],
    query: str,
    model: SentenceTransformer,
    budget_ratio: float,
) -> list[dict]:
    """Prune sentences to meet token budget while preserving connectivity.

    1. Score all nodes
    2. Identify anchor nodes (top-scoring, query-relevant)
    3. Iteratively remove lowest-scoring non-anchor nodes that
       don't disconnect the anchor subgraph
    4. Stop when token budget is met

    Returns the surviving sentences in original order.
    """
    if not sentences or not G.nodes:
        return sentences

    scores = _score_nodes(G, query, model, sentences)

    total_tokens = sum(s["token_count"] for s in sentences if s["idx"] in scores)
    target_tokens = int(total_tokens * budget_ratio)

    # Anchor nodes: top 30% by score (never removed)
    sorted_nodes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    n_anchors = max(2, len(sorted_nodes) // 3)
    anchor_ids = set(nid for nid, _ in sorted_nodes[:n_anchors])

    # Current surviving set
    surviving = set(scores.keys())
    sent_map = {s["idx"]: s for s in sentences}

    # Iteratively prune lowest-scoring non-anchor nodes
    candidates = sorted(
        [(nid, sc) for nid, sc in scores.items() if nid not in anchor_ids],
        key=lambda x: x[1],
    )

    for nid, _ in candidates:
        current_tokens = sum(sent_map[s]["token_count"] for s in surviving if s in sent_map)
        if current_tokens <= target_tokens:
            break

        # Check if removing this node disconnects anchors
        test_set = surviving - {nid}
        if _anchors_connected(G, test_set, anchor_ids):
            surviving.discard(nid)

    # Return sentences in original order
    result = [sent_map[nid] for nid in sorted(surviving) if nid in sent_map]
    return result


def _anchors_connected(G: nx.Graph, surviving: set, anchor_ids: set) -> bool:
    """Check that removing a node does not disconnect anchor pairs that were connected in G."""
    surviving_anchors = list(anchor_ids & surviving)
    if len(surviving_anchors) <= 1:
        return True

    subgraph = G.subgraph(surviving)
    # Only verify pairs that were connected in the original graph
    for i in range(len(surviving_anchors)):
        for j in range(i + 1, len(surviving_anchors)):
            a1, a2 = surviving_anchors[i], surviving_anchors[j]
            if nx.has_path(G, a1, a2) and not nx.has_path(subgraph, a1, a2):
                return False
    return True
