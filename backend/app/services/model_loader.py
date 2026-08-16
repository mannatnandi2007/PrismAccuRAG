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


class ModelLoader:
    """Lazy-initialised singleton for all ML models with minimal memory footprint."""

    _instance: ModelLoader | None = None

    def __init__(self):
        self._embedding_model = None
        self._spacy_nlp = None
        self._nli_model = None

    @classmethod
    def get(cls) -> ModelLoader:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def embedding_model(self):
        if self._embedding_model is None:
            import torch
            torch.set_num_threads(1)
            torch.set_grad_enabled(False)
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model on CPU: {settings.embedding_model}")
            self._embedding_model = SentenceTransformer(settings.embedding_model, device="cpu")
            gc.collect()
            logger.info("Embedding model loaded")
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
        if self._nli_model is None:
            logger.info(f"Loading NLI model on CPU: {settings.nli_model}")
            try:
                import torch
                torch.set_num_threads(1)
                torch.set_grad_enabled(False)
                from sentence_transformers.cross_encoder import CrossEncoder
                self._nli_model = CrossEncoder(settings.nli_model, device="cpu")
            except Exception as e:
                logger.warning(f"Could not load CrossEncoder ({e}), using fallback")
                self._nli_model = None
            gc.collect()
            logger.info("NLI model loaded")
        return self._nli_model

    def warmup(self):
        """Lightweight warmup without spiking memory."""
        gc.collect()

