"""End-to-end pipeline orchestrator — runs all 10 stages and collects metrics."""

from __future__ import annotations

import logging
import time

import faiss

from app.config import settings
from app.models import (
    QueryResponse, TokenStats, ClaimResult, LatencyBreakdown,
)
from app.services.model_loader import ModelLoader
from app.pipeline.ingestion import chunk_documents, embed_chunks, build_faiss_index
from app.pipeline.retrieval import retrieve
from app.pipeline.coref import resolve_coreferences
from app.pipeline.graph import build_sentence_graph
from app.pipeline.classifier import classify_query
from app.pipeline.pruning import prune_graph
from app.pipeline.claims import extract_claims
from app.pipeline.entailment import verify_claims
from app.pipeline.repair import repair_context
from app.pipeline.generation import generate_answer

logger = logging.getLogger(__name__)


# ── In-memory & cached store for ingested data ─────────────────────────────────

import json
import os
import tempfile

CACHE_FILE = os.path.join(tempfile.gettempdir(), "prism_doc_cache.json")


class DocumentStore:
    """In-memory store for chunks + FAISS index, with automatic disk cache."""

    def __init__(self):
        self.chunks: list[dict] = []
        self.index: faiss.IndexFlatIP | None = None
        self.total_tokens: int = 0
        self.raw_docs: list[str] = []
        self._load_cache()

    def _load_cache(self):
        """Attempt to restore previously ingested documents from cache on startup."""
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("documents"):
                        self.raw_docs = data["documents"]
                        # Note: FAISS will be lazily or synchronously rebuilt
        except Exception as e:
            logger.warning(f"Could not load doc cache: {e}")

    def ensure_indexed(self):
        """Ensure FAISS index is built if documents were loaded from cache."""
        if (self.index is None or len(self.chunks) == 0) and self.raw_docs:
            self.ingest(self.raw_docs, save_cache=False)

    def ingest(self, documents: list[str], save_cache: bool = True) -> dict:
        """Chunk, embed, and index documents."""
        ml = ModelLoader.get()

        self.raw_docs = documents
        self.chunks = chunk_documents(documents)
        embeddings = embed_chunks(self.chunks, ml.embedding_model)
        self.index = build_faiss_index(embeddings)
        self.total_tokens = sum(c["token_count"] for c in self.chunks)

        if save_cache:
            try:
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump({"documents": documents}, f)
            except Exception as e:
                logger.warning(f"Could not save doc cache: {e}")

        return {
            "doc_count": len(documents),
            "chunk_count": len(self.chunks),
            "total_tokens": self.total_tokens,
        }

    @property
    def is_ready(self) -> bool:
        self.ensure_indexed()
        return self.index is not None and len(self.chunks) > 0


# Global store
doc_store = DocumentStore()


def _timer():
    """Return a context-like timer."""
    return _Timer()


class _Timer:
    def __init__(self):
        self.start = 0.0
        self.elapsed_ms = 0.0

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed_ms = (time.perf_counter() - self.start) * 1000


# ── Main pipeline ────────────────────────────────────────────────────────────

def run_pipeline(query: str, top_k: int | None = None) -> QueryResponse:
    """Execute the full 10-stage RAG compression pipeline."""

    if not doc_store.is_ready:
        raise ValueError("No documents ingested. Please ingest documents first.")

    ml = ModelLoader.get()
    latency = {}
    total_start = time.perf_counter()

    # 1. Retrieval
    with _timer() as t:
        retrieved = retrieve(query, doc_store.index, doc_store.chunks, ml.embedding_model, top_k)
    latency["retrieval_ms"] = t.elapsed_ms

    if not retrieved:
        raise ValueError("No relevant chunks found for this query.")

    original_tokens = sum(c["token_count"] for c in retrieved)

    # 2. Cross-chunk coreference
    with _timer() as t:
        sentences, clusters, combined_text = resolve_coreferences(retrieved, ml.nlp)
    latency["coref_ms"] = t.elapsed_ms

    # 3. Build dependency graph
    with _timer() as t:
        graph = build_sentence_graph(sentences, clusters)
    latency["graph_build_ms"] = t.elapsed_ms

    # 4. Query classification
    with _timer() as t:
        query_type, budget_ratio = classify_query(query, ml.embedding_model)
    latency["classification_ms"] = t.elapsed_ms

    # 5. Graph pruning
    with _timer() as t:
        pruned_sentences = prune_graph(graph, sentences, query, ml.embedding_model, budget_ratio)
    latency["pruning_ms"] = t.elapsed_ms

    compressed_text = " ".join(s["text"] for s in pruned_sentences)
    compressed_tokens = sum(s["token_count"] for s in pruned_sentences)

    # 6. Claim extraction (on original retrieved text)
    with _timer() as t:
        claims = extract_claims(combined_text, ml.nlp)
    latency["claim_extraction_ms"] = t.elapsed_ms

    # 7. Entailment verification (against compressed text)
    nli = ml.nli_model  # May be None if memory was insufficient
    if nli is None:
        logger.info("NLI model unavailable — entailment verification will be skipped")
    with _timer() as t:
        entailment_results = verify_claims(claims, compressed_text, nli)
    latency["entailment_ms"] = t.elapsed_ms

    # 8. Surgical repair
    with _timer() as t:
        compressed_sents = [s["text"] for s in pruned_sentences]
        repaired_context, claim_results = repair_context(
            compressed_sents,
            entailment_results,
            ml.nli_model,
            settings.entailment_threshold,
        )
    latency["repair_ms"] = t.elapsed_ms

    final_tokens = len(repaired_context.split())

    # 9. LLM answer generation
    with _timer() as t:
        answer = generate_answer(query, repaired_context)
    latency["generation_ms"] = t.elapsed_ms

    total_ms = (time.perf_counter() - total_start) * 1000
    latency["total_ms"] = total_ms

    # 10. Assemble response
    token_stats = TokenStats(
        original_tokens=original_tokens,
        compressed_tokens=compressed_tokens,
        final_tokens=final_tokens,
        percent_saved=round((1 - final_tokens / max(original_tokens, 1)) * 100, 1),
    )

    total_claims = len(claim_results)
    passed = sum(1 for c in claim_results if c.status in ("preserved", "repaired"))
    entailment_pass_rate = round(passed / max(total_claims, 1) * 100, 1)

    latency_obj = LatencyBreakdown(**latency)

    return QueryResponse(
        answer=answer,
        query_type=query_type,
        token_stats=token_stats,
        entailment_pass_rate=entailment_pass_rate,
        claims=claim_results,
        latency=latency_obj,
        compressed_context=repaired_context,
    )
