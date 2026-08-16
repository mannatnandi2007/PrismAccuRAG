"""LLM answer generation via Groq (free tier)."""

from __future__ import annotations

import logging
import os
from groq import Groq

from app.config import settings

logger = logging.getLogger(__name__)

_client: Groq | None = None
_cached_key: str | None = None


def _get_client() -> Groq:
    global _client, _cached_key
    # Force search and reload .env from all candidate locations
    from dotenv import load_dotenv
    for p in [".env", "../.env", "../../.env", os.path.join(os.path.dirname(__file__), "../../../.env"), os.path.join(os.path.dirname(__file__), "../../.env")]:
        if os.path.exists(p):
            load_dotenv(p, override=True)
            break

    api_key = settings.groq_api_key or os.getenv("GROQ_API_KEY", "")
    # Clean up quotes or whitespace
    api_key = api_key.strip().strip("'").strip('"')

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is missing or empty. Please check your .env file or environment variables."
        )
    if _client is None or _cached_key != api_key:
        _client = Groq(api_key=api_key)
        _cached_key = api_key
    return _client


def generate_answer(query: str, context: str) -> str:
    """Send compressed context + query to Groq for answer generation.

    Single API call on compressed context, with automatic model fallback.
    """
    client = _get_client()

    system_prompt = (
        "You are a concise, factual research assistant. "
        "Answer the user's question directly based ONLY on the provided context. "
        "Do NOT output internal thinking or reasoning logs. Provide only the final answer text."
    )

    user_prompt = f"""Context:
{context}

Question: {query}

Provide a direct, concise answer based only on the context:"""

    # List of models to try in order (configured model first, then known active free models)
    primary_model = settings.groq_model
    fallback_models = [
        primary_model,
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "qwen/qwen3.6-27b",
        "meta-llama/llama-4-scout-17b-16e-instruct",
    ]
    
    models_to_try = []
    for m in fallback_models:
        if m and m not in models_to_try:
            models_to_try.append(m)

    last_error = None
    for model_name in models_to_try:
        try:
            logger.info(f"Attempting LLM generation with Groq model: {model_name}")
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=2048,
            )
            raw_answer = response.choices[0].message.content.strip()
            
            # Robustly clean out <think> tags (even unclosed ones from reasoning models)
            import re
            if "<think>" in raw_answer:
                if "</think>" in raw_answer:
                    clean = re.sub(r"<think>.*?</think>", "", raw_answer, flags=re.DOTALL).strip()
                    answer = clean if clean else raw_answer
                else:
                    # Unclosed think tag: extract whatever conclusion was drafted or strip think prefix
                    match = re.search(r'(?:final answer|output generation|draft:?)\s*[:\-]?\s*["\']?(.*)', raw_answer, flags=re.IGNORECASE | re.DOTALL)
                    if match and match.group(1).strip():
                        answer = match.group(1).strip().strip('"\'')
                    else:
                        answer = re.sub(r"^<think>\s*", "", raw_answer).strip()
            else:
                answer = raw_answer

            logger.info(f"Successfully generated answer ({len(answer)} chars) via {model_name}")
            return answer
        except Exception as e:
            last_error = e
            err_msg = str(e).lower()
            logger.warning(f"Model {model_name} failed: {e}. Trying fallback if available...")
            if "invalid api key" in err_msg or "authentication" in err_msg or "401" in err_msg:
                raise RuntimeError(f"Groq Authentication failed: {e}") from e

    logger.error(f"All Groq models failed. Last error: {last_error}")
    raise RuntimeError(f"LLM generation failed across all attempted models: {last_error}") from last_error

