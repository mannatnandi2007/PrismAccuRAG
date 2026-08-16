"""Cross-chunk coreference resolution and entity linking.

Uses spaCy NER-based entity matching as the primary approach (robust,
no extra model downloads). Optionally tries fastcoref if installed.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field

import spacy

logger = logging.getLogger(__name__)


@dataclass
class CorefCluster:
    """A cluster of mentions that refer to the same entity."""
    canonical: str
    mentions: list[dict] = field(default_factory=list)  # {text, sent_idx, start, end}


def _split_sentences(nlp, text: str) -> list[dict]:
    """Split text into sentences with character offsets."""
    doc = nlp(text)
    sentences = []
    for i, sent in enumerate(doc.sents):
        sentences.append({
            "idx": i,
            "text": sent.text.strip(),
            "start": sent.start_char,
            "end": sent.end_char,
        })
    return sentences


def resolve_coreferences(
    chunks: list[dict],
    nlp,
) -> tuple[list[dict], list[CorefCluster], str]:
    """Run entity-based coreference across retrieved chunks.

    Returns:
        sentences: list of sentence dicts
        clusters: list of CorefCluster
        combined_text: the joined text
    """
    # Combine all chunks into one text block
    combined_text = " ".join(c["text"] for c in chunks)

    # Parse with spaCy
    doc = nlp(combined_text)

    # Extract sentences
    sentences = []
    for i, sent in enumerate(doc.sents):
        sentences.append({
            "idx": i,
            "text": sent.text.strip(),
            "start_char": sent.start_char,
            "end_char": sent.end_char,
            "token_count": len(sent.text.split()),
        })

    # Build entity → sentence mapping (entity-based coref)
    entity_map: dict[str, list[dict]] = defaultdict(list)

    for ent in doc.ents:
        # Normalise entity text
        canonical = ent.text.strip().lower()
        # Find which sentence this entity belongs to
        for sent in sentences:
            if ent.start_char >= sent["start_char"] and ent.end_char <= sent["end_char"]:
                entity_map[canonical].append({
                    "text": ent.text,
                    "sent_idx": sent["idx"],
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "label": ent.label_,
                })
                break

    # Also do pronoun-to-nearest-entity linking (simple heuristic)
    _link_pronouns(doc, sentences, entity_map)

    # Build clusters (only entities appearing in 2+ sentences)
    clusters = []
    for canonical, mentions in entity_map.items():
        unique_sents = set(m["sent_idx"] for m in mentions)
        if len(unique_sents) >= 2:
            clusters.append(CorefCluster(canonical=canonical, mentions=mentions))

    logger.info(f"Coref: {len(clusters)} cross-sentence clusters from {len(sentences)} sentences")
    return sentences, clusters, combined_text


def _link_pronouns(doc, sentences: list[dict], entity_map: dict):
    """Simple heuristic: link pronouns to the closest preceding named entity."""
    pronouns = {"he", "she", "it", "they", "him", "her", "them", "his", "its", "their"}
    
    last_entity = None
    for token in doc:
        if token.ent_type_:
            last_entity = token.text.strip().lower()
        elif token.text.lower() in pronouns and last_entity:
            # Find sentence index
            for sent in sentences:
                if token.idx >= sent["start_char"] and token.idx < sent["end_char"]:
                    entity_map[last_entity].append({
                        "text": token.text,
                        "sent_idx": sent["idx"],
                        "start": token.idx,
                        "end": token.idx + len(token.text),
                        "label": "PRONOUN",
                    })
                    break
