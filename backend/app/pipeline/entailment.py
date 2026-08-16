"""Post-compression entailment verification using a local NLI model."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.config import settings
from app.pipeline.claims import Claim

logger = logging.getLogger(__name__)


@dataclass
class EntailmentResult:
    claim: Claim
    entailment_score: float
    passed: bool


def verify_claims(
    claims: list[Claim],
    compressed_context: str,
    nli_model,
) -> list[EntailmentResult]:
    """Check each claim against the compressed context using NLI.

    The cross-encoder model returns scores for [contradiction, neutral, entailment].
    We use the entailment score (index 2) as our confidence measure.
    """
    if not claims:
        return []

    results: list[EntailmentResult] = []

    # Build premise-hypothesis pairs
    pairs = [(compressed_context, c.claim_text) for c in claims]

    # Batch predict
    try:
        raw_scores = nli_model.predict(pairs, apply_softmax=True)
    except Exception as e:
        logger.warning(f"NLI batch prediction failed, falling back to individual: {e}")
        raw_scores = []
        for pair in pairs:
            try:
                score = nli_model.predict([pair], apply_softmax=True)
                raw_scores.append(score[0])
            except Exception:
                raw_scores.append([0.33, 0.34, 0.33])  # neutral fallback

    for claim, scores in zip(claims, raw_scores):
        # scores: [contradiction, neutral, entailment]
        if hasattr(scores, "__len__") and len(scores) >= 3:
            entailment_score = float(scores[2])
        else:
            # Single-score model
            entailment_score = float(scores) if not hasattr(scores, "__len__") else float(scores[0])

        passed = entailment_score >= settings.entailment_threshold

        results.append(EntailmentResult(
            claim=claim,
            entailment_score=entailment_score,
            passed=passed,
        ))

    pass_count = sum(1 for r in results if r.passed)
    logger.info(f"Entailment: {pass_count}/{len(results)} claims passed (threshold={settings.entailment_threshold})")

    return results
