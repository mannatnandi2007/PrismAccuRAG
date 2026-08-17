"""FastAPI application — routes, CORS, startup."""

from __future__ import annotations
# v1.0.2 - deployment fixes, memory-safe health check, static mount guard

import logging
import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import IngestRequest, IngestResponse, QueryRequest, QueryResponse
from app.services.model_loader import ModelLoader, _get_memory_usage_mb
from app.services.orchestrator import doc_store, run_pipeline

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-30s │ %(levelname)-5s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── App lifecycle ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Asynchronously warm up models in background thread so uvicorn binds port instantly
    # and models are ready in RAM when the user clicks Ingest
    def _bg_warmup():
        try:
            logger.info("Background model loading started...")
            ml = ModelLoader.get()
            ml._models_warming = True
            _ = ml.embedding_model
            _ = ml.nlp
            # NLI model is optional — load only if memory allows
            _ = ml.nli_model
            ml._models_ready = True
            ml._models_warming = False
            logger.info("Background model loading complete - ready for requests")
        except Exception as e:
            ml._models_warming = False
            logger.warning(f"Background warmup warning: {e}")

    threading.Thread(target=_bg_warmup, daemon=True).start()
    logger.info("PrismAccuRAG ready (port bound, models loading in background)")
    yield
    logger.info("Shutting down")


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="PrismAccuRAG API",
    description="Accuracy-preserving adaptive RAG context compression pipeline",
    version="1.0.2",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    return {
        "status": "online",
        "service": "PrismAccuRAG API",
        "version": "1.0.2",
        "health": "/api/health",
        "docs": "/docs"
    }


@app.api_route("/health", methods=["GET", "HEAD"])
async def health_ping():
    return {"status": "ok"}


@app.api_route("/api/health", methods=["GET", "HEAD"])
async def health():
    """Health check that does NOT trigger model loading.
    
    Reports whether models are loaded without lazy-initialising them.
    This prevents Render's health probe from causing OOM spikes.
    """
    ml = ModelLoader.get()
    mem_mb = _get_memory_usage_mb()
    return {
        "status": "healthy",
        "models_loaded": ml.is_ready,
        "models_warming": ml._models_warming,
        "embedding_loaded": ml.embedding_loaded,
        "nli_available": ml.nli_available,
        "nli_skipped": ml._nli_skipped,
        "documents_ingested": doc_store.index is not None and len(doc_store.chunks) > 0,
        "chunk_count": len(doc_store.chunks),
        "total_tokens": doc_store.total_tokens,
        "memory_mb": round(mem_mb, 1) if mem_mb > 0 else None,
    }


@app.post("/api/ingest", response_model=IngestResponse)
def ingest_documents(req: IngestRequest):
    """Ingest documents: chunk, embed, and index in FAISS (runs in threadpool)."""
    try:
        result = doc_store.ingest(req.documents)
        return IngestResponse(**result)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query", response_model=QueryResponse)
def query_pipeline(req: QueryRequest):
    """Run the full RAG compression pipeline on a query (runs in threadpool)."""
    if not doc_store.is_ready:
        raise HTTPException(status_code=400, detail="No documents ingested. Please ingest documents first.")

    try:
        result = run_pipeline(req.query, req.top_k)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


# ── Static UI Mounting (for unified single-container / Render deployment) ──────

from fastapi.staticfiles import StaticFiles

# Candidate paths for frontend build
_possible_dist_paths = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../frontend/dist")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist")),
    os.path.abspath("frontend/dist"),
    os.path.abspath("../frontend/dist"),
]

for dist_path in _possible_dist_paths:
    if os.path.exists(dist_path) and os.path.isfile(os.path.join(dist_path, "index.html")):
        logger.info(f"Serving frontend static files from: {dist_path}")
        # Mount at /assets and /static first for explicit static file paths,
        # then mount the catch-all at / AFTER all API routes are registered.
        # FastAPI processes routes in registration order, so API routes above
        # will match before the static catch-all.
        app.mount("/", StaticFiles(directory=dist_path, html=True), name="frontend")
        break
