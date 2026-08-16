"""Extract atomic claims as subject-predicate-object triples via spaCy dependency parsing."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import spacy

logger = logging.getLogger(__name__)


@dataclass
class Claim:
    subject: str
    predicate: str
    object: str
    claim_text: str        # human-readable "subject predicate object"
    source_sentence: str   # original sentence this came from


def extract_claims(text: str, nlp) -> list[Claim]:
    """Extract SPO triples from text using spaCy dependency parsing.

    Strategy:
    - Find verbs (ROOT or relcl)
    - Walk left for nsubj → subject
    - Walk right for dobj / attr / prep+pobj → object
    - Form claim text as "subject predicate object"
    """
    doc = nlp(text)
    claims: list[Claim] = []

    for sent in doc.sents:
        sent_text = sent.text.strip()
        if not sent_text:
            continue

        for token in sent:
            # Find main verbs
            if token.pos_ not in ("VERB", "AUX") or token.dep_ not in ("ROOT", "relcl", "ccomp", "xcomp", "advcl"):
                if token.dep_ != "ROOT":
                    continue

            verb = token
            subject = None
            obj = None

            # Find subject
            for child in verb.children:
                if child.dep_ in ("nsubj", "nsubjpass"):
                    subject = _get_subtree_text(child)
                    break

            if not subject:
                continue

            # Find object
            for child in verb.children:
                if child.dep_ in ("dobj", "attr", "oprd"):
                    obj = _get_subtree_text(child)
                    break
                elif child.dep_ == "prep":
                    for grandchild in child.children:
                        if grandchild.dep_ == "pobj":
                            obj = child.text + " " + _get_subtree_text(grandchild)
                            break
                    if obj:
                        break

            if not obj:
                # Try acomp or other complements
                for child in verb.children:
                    if child.dep_ in ("acomp", "ccomp"):
                        obj = _get_subtree_text(child)
                        break

            if subject and obj:
                # Include auxiliary verbs
                predicate = _get_verb_phrase(verb)
                claim_text = f"{subject} {predicate} {obj}"
                claims.append(Claim(
                    subject=subject,
                    predicate=predicate,
                    object=obj,
                    claim_text=claim_text,
                    source_sentence=sent_text,
                ))

    logger.info(f"Extracted {len(claims)} claims from {len(list(doc.sents))} sentences")
    return claims


def _get_subtree_text(token) -> str:
    """Get the full text of a token's subtree (contiguous span)."""
    subtree = sorted(token.subtree, key=lambda t: t.i)
    return " ".join(t.text for t in subtree)


def _get_verb_phrase(verb) -> str:
    """Get verb + auxiliaries + particles as a phrase."""
    parts = []
    for child in verb.children:
        if child.dep_ in ("aux", "auxpass", "neg") and child.i < verb.i:
            parts.append((child.i, child.text))
    parts.append((verb.i, verb.text))
    for child in verb.children:
        if child.dep_ == "prt":
            parts.append((child.i, child.text))
    parts.sort(key=lambda x: x[0])
    return " ".join(p[1] for p in parts)
