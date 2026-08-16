"""Singleton model loader — loads all ML models once at startup."""

from __future__ import annotations

import logging
import spacy
from sentence_transformers import SentenceTransformer
from sentence_transformers.cross_encoder import CrossEncoder

from app.config import settings

logger = logging.getLogger(__name__)


class ModelLoader:
    """Lazy-initialised singleton for all ML models."""

    _instance: ModelLoader | None = None

    def __init__(self):
        self._embedding_model: SentenceTransformer | None = None
        self._spacy_nlp = None
        self._nli_model = None

    @classmethod
    def get(cls) -> ModelLoader:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def embedding_model(self) -> SentenceTransformer:
        if self._embedding_model is None:
            logger.info(f"Loading embedding model: {settings.embedding_model}")
            self._embedding_model = SentenceTransformer(settings.embedding_model)
            logger.info("Embedding model loaded")
        return self._embedding_model

    @property
    def nlp(self):
        if self._spacy_nlp is None:
            logger.info(f"Loading spaCy model: {settings.spacy_model}")
            self._spacy_nlp = spacy.load(settings.spacy_model)
            logger.info("spaCy model loaded")
        return self._spacy_nlp

    @property
    def nli_model(self):
        if self._nli_model is None:
            logger.info(f"Loading NLI model: {settings.nli_model}")
            self._nli_model = CrossEncoder(settings.nli_model)
            logger.info("NLI model loaded")
        return self._nli_model

    def warmup(self):
        """Pre-load all models (call at startup)."""
        logger.info("Warming up models...")
        _ = self.embedding_model
        _ = self.nlp
        _ = self.nli_model
        logger.info("All models loaded and ready")
