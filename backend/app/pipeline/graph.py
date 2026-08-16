"""Build a sentence-level dependency graph using NetworkX."""

from __future__ import annotations

import re
import networkx as nx

from app.pipeline.coref import CorefCluster


def build_sentence_graph(
    sentences: list[dict],
    clusters: list[CorefCluster],
) -> nx.Graph:
    """Build an undirected graph where:
    - Nodes = sentences (with metadata)
    - Edges = shared entity / coreference cluster between sentences

    Node attributes:
        text, token_count, entity_count, has_numbers, has_citations
    Edge attributes:
        shared_entities (list of canonical entity names linking the pair)
    """
    G = nx.Graph()

    # Add nodes
    for sent in sentences:
        text = sent["text"]
        G.add_node(
            sent["idx"],
            text=text,
            token_count=sent["token_count"],
            entity_count=0,  # will be updated
            has_numbers=bool(re.search(r"\d+\.?\d*", text)),
            has_citations=bool(re.search(r"\[\d+\]|\(\d{4}\)|et al\.", text)),
        )

    # Count entities per sentence
    for cluster in clusters:
        seen_sents = set()
        for mention in cluster.mentions:
            sid = mention["sent_idx"]
            if sid in G and sid not in seen_sents:
                G.nodes[sid]["entity_count"] += 1
                seen_sents.add(sid)

    # Add edges between sentences sharing a coref cluster
    for cluster in clusters:
        sent_ids = sorted(set(m["sent_idx"] for m in cluster.mentions if m["sent_idx"] in G))
        for i in range(len(sent_ids)):
            for j in range(i + 1, len(sent_ids)):
                u, v = sent_ids[i], sent_ids[j]
                if G.has_edge(u, v):
                    G.edges[u, v]["shared_entities"].append(cluster.canonical)
                else:
                    G.add_edge(u, v, shared_entities=[cluster.canonical])

    return G
