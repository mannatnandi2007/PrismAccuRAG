"""Pydantic request / response schemas for the API."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ── Requests ──────────────────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    """Accept a list of raw document texts."""
    documents: list[str] = Field(..., min_length=1, description="List of document texts to ingest")


class QueryRequest(BaseModel):
    """Accept a user query and optional overrides."""
    query: str = Field(..., min_length=1, description="The user's question")
    top_k: Optional[int] = Field(None, ge=1, le=20, description="Override default top-k retrieval count")


# ── Response sub-models ───────────────────────────────────────────────────────

class TokenStats(BaseModel):
    original_tokens: int
    compressed_tokens: int
    final_tokens: int  # after repair
    percent_saved: float


class ClaimResult(BaseModel):
    claim_text: str
    status: str  # "preserved" | "repaired" | "dropped"
    entailment_score: float
    source_sentence: str


class LatencyBreakdown(BaseModel):
    ingestion_ms: float = 0.0
    retrieval_ms: float = 0.0
    coref_ms: float = 0.0
    graph_build_ms: float = 0.0
    classification_ms: float = 0.0
    pruning_ms: float = 0.0
    claim_extraction_ms: float = 0.0
    entailment_ms: float = 0.0
    repair_ms: float = 0.0
    generation_ms: float = 0.0
    total_ms: float = 0.0


# ── Responses ─────────────────────────────────────────────────────────────────

class IngestResponse(BaseModel):
    doc_count: int
    chunk_count: int
    total_tokens: int
    message: str = "Documents ingested successfully"


class QueryResponse(BaseModel):
    answer: str
    query_type: str  # "factoid" | "multi-hop"
    token_stats: TokenStats
    entailment_pass_rate: float
    claims: list[ClaimResult]
    latency: LatencyBreakdown
    compressed_context: str  # for transparency
