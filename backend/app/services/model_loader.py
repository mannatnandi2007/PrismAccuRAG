from __future__ import annotations

import os
import gc
import logging

# Constrain PyTorch and OpenMP thread memory overhead on Render's 512MB limit
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from app.config import settings

logger = logging.getLogger(__name__)

# Minimum free memory (in MB) required to attempt loading the NLI model
_NLI_MIN_FREE_MB = 350


def _get_memory_usage_mb() -> float:
    """Return current process RSS in MB (cross-platform)."""
    try:
        import resource
        # Unix / Linux / macOS
        usage_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # macOS reports bytes, Linux reports KB
        import sys
        if sys.platform == "darwin":
            return usage_kb / (1024 * 1024)
        return usage_kb / 1024
    except ImportError:
        pass
    try:
        # Windows fallback
        import psutil
        return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    except ImportError:
        return -1.0


def _get_available_memory_mb() -> float:
    """Estimate available memory for the process in MB."""
    try:
        import psutil
        return psutil.virtual_memory().available / (1024 * 1024)
    except ImportError:
        pass
    try:
        # Linux: read from /proc/meminfo
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) / 1024  # KB → MB
    except (FileNotFoundError, ValueError):
        pass
    # Cannot determine — assume enough
    return 9999.0


class ModelLoader:
    """Lazy-initialised singleton for all ML models with minimal memory footprint."""

    _instance: ModelLoader | None = None

    def __init__(self):
        self._embedding_model = None
        self._spacy_nlp = None
        self._nli_model = None
        self._nli_skipped = False  # True if NLI was intentionally skipped (not a failure)
        self._models_warming = False
        self._models_ready = False

    @classmethod
    def get(cls) -> ModelLoader:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def is_ready(self) -> bool:
        """Check if essential models (embedding + spaCy) are loaded."""
        return self._embedding_model is not None and self._spacy_nlp is not None

    @property
    def embedding_loaded(self) -> bool:
        return self._embedding_model is not None

    @property
    def nli_available(self) -> bool:
        """True if NLI model is loaded and usable."""
        return self._nli_model is not None and not self._nli_skipped

    @property
    def embedding_model(self):
        if self._embedding_model is None:
            import torch
            torch.set_num_threads(1)
            torch.set_grad_enabled(False)
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model on CPU: {settings.embedding_model}")
            mem_before = _get_memory_usage_mb()
            self._embedding_model = SentenceTransformer(settings.embedding_model, device="cpu")
            gc.collect()
            mem_after = _get_memory_usage_mb()
            logger.info(f"Embedding model loaded (RSS: {mem_before:.0f}MB → {mem_after:.0f}MB)")
        return self._embedding_model

    @property
    def nlp(self):
        if self._spacy_nlp is None:
            import spacy
            logger.info(f"Loading spaCy model: {settings.spacy_model}")
            self._spacy_nlp = spacy.load(settings.spacy_model)
            gc.collect()
            logger.info("spaCy model loaded")
        return self._spacy_nlp

    @property
    def nli_model(self):
        """Load the NLI model if memory allows, otherwise return None gracefully."""
        if self._nli_model is None and not self._nli_skipped:
            available_mb = _get_available_memory_mb()
            current_mb = _get_memory_usage_mb()
            logger.info(f"NLI load check — available: {available_mb:.0f}MB, current RSS: {current_mb:.0f}MB")

            if available_mb < _NLI_MIN_FREE_MB:
                logger.warning(
                    f"Skipping NLI model — only {available_mb:.0f}MB available "
                    f"(need {_NLI_MIN_FREE_MB}MB). Entailment verification will be bypassed."
                )
                self._nli_skipped = True
                return None

            try:
                import torch
                torch.set_num_threads(1)
                torch.set_grad_enabled(False)
                from sentence_transformers.cross_encoder import CrossEncoder
                logger.info(f"Loading NLI model on CPU: {settings.nli_model}")
                mem_before = _get_memory_usage_mb()
                self._nli_model = CrossEncoder(settings.nli_model, device="cpu")
                gc.collect()
                mem_after = _get_memory_usage_mb()
                logger.info(f"NLI model loaded (RSS: {mem_before:.0f}MB → {mem_after:.0f}MB)")
            except Exception as e:
                logger.warning(f"Could not load NLI model ({e}). Entailment verification will be bypassed.")
                self._nli_skipped = True
                self._nli_model = None
            gc.collect()
        return self._nli_model

    def warmup(self):
        """Lightweight warmup without spiking memory."""
        gc.collect()
