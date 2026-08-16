import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Search for .env in current directory, parent directory, and project root
_possible_env_paths = [
    os.path.abspath(".env"),
    os.path.abspath("../.env"),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.env")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env")),
]

for p in _possible_env_paths:
    if os.path.exists(p):
        load_dotenv(p, override=True)
        break


@dataclass
class Settings:
    """Central configuration for the RAG Compressor pipeline."""

    # --- LLM (Groq) ---
    @property
    def groq_api_key(self) -> str:
        return os.getenv("GROQ_API_KEY", "").strip()

    @property
    def groq_model(self) -> str:
        return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()

    # --- Embedding model ---
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # --- spaCy ---
    spacy_model: str = "en_core_web_sm"

    # --- NLI / Entailment ---
    nli_model: str = "cross-encoder/nli-deberta-v3-small"
    entailment_threshold: float = 0.65

    # --- Chunking ---
    chunk_size: int = 250        # tokens per chunk
    chunk_overlap: int = 50      # overlap tokens between chunks

    # --- Retrieval ---
    top_k: int = 5

    # --- Pruning budgets (fraction of tokens to KEEP) ---
    factoid_budget: float = 0.30
    multihop_budget: float = 0.60

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000


settings = Settings()

