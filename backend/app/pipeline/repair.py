"""Surgical repair: re-insert source sentences for failed claims."""

from __future__ import annotations

import logging
from app.pipeline.entailment import EntailmentResult
from app.models import ClaimResult

logger = logging.getLogger(__name__)


def repair_context(
    compressed_sentences: list[str],
    entailment_results: list[EntailmentResult],
    nli_model,
    entailment_threshold: float,
) -> tuple[str, list[ClaimResult]]:
    """For each failed claim, re-insert its source sentence into the context.

    Returns:
        repaired_context: the final compressed + repaired text
        claim_results: list of ClaimResult with status tags
    
    If entailment was skipped (all results have passed=True with score=1.0),
    this effectively becomes a no-op — all claims are "preserved" and no
    re-insertion is needed.
    """
    # Start with the compressed context sentences
    context_parts = list(compressed_sentences)
    inserted_sentences = set()
    claim_results: list[ClaimResult] = []

    for er in entailment_results:
        if er.passed:
            claim_results.append(ClaimResult(
                claim_text=er.claim.claim_text,
                status="preserved",
                entailment_score=er.entailment_score,
                source_sentence=er.claim.source_sentence,
            ))
        else:
            # Re-insert the source sentence
            src = er.claim.source_sentence.strip()
            if src and src not in inserted_sentences:
                context_parts.append(src)
                inserted_sentences.add(src)
                logger.info(f"Repair: re-inserted sentence for claim '{er.claim.claim_text[:60]}...'")

            claim_results.append(ClaimResult(
                claim_text=er.claim.claim_text,
                status="repaired",
                entailment_score=er.entailment_score,
                source_sentence=er.claim.source_sentence,
            ))

    repaired_context = " ".join(context_parts)

    # Optionally re-verify repaired claims
    repaired_count = sum(1 for c in claim_results if c.status == "repaired")
    logger.info(f"Repair: {repaired_count} claims repaired, {len(inserted_sentences)} sentences re-inserted")

    return repaired_context, claim_results
