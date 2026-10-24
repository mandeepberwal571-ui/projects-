"""
Gemini Embedder module using the official google-genai SDK.
Supports batching, exponential backoff for rate limits,
and task_type specification (RETRIEVAL_DOCUMENT vs RETRIEVAL_QUERY).
"""

import logging
import random
import time
from typing import Any, Callable, List, Optional
from google import genai
from google.genai import types

from src.retrieval.config import (
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_DIMENSION,
    EMBEDDING_MODEL,
    validate_api_key,
)

logger = logging.getLogger(__name__)


class GeminiEmbedder:
    """
    Client for generating embeddings using the google-genai SDK.
    """

    def __init__(
        self,
        model_name: str = EMBEDDING_MODEL,
        output_dimensionality: int = EMBEDDING_DIMENSION,
        api_key: Optional[str] = None
    ):
        self.api_key = api_key or validate_api_key()
        self.model_name = model_name
        self.output_dimensionality = output_dimensionality
        self.client = genai.Client(api_key=self.api_key)

    def _execute_with_retry(
        self,
        call_fn: Callable[[], Any],
        max_retries: int = 6,
        initial_delay: float = 2.0
    ) -> Any:
        """Execute a call with exponential backoff on 429 / 503 / 500 errors."""
        for attempt in range(max_retries):
            try:
                return call_fn()
            except Exception as exc:
                err_msg = str(exc)
                is_retryable = any(
                    code in err_msg.lower()
                    for code in ["429", "resource_exhausted", "quota", "503", "500", "overloaded"]
                )
                if is_retryable and attempt < max_retries - 1:
                    sleep_sec = (initial_delay * (2 ** attempt)) + random.uniform(0.5, 1.5)
                    logger.warning(
                        "Rate limit or transient error encountered: %s. Retrying in %.1fs (attempt %d/%d)...",
                        err_msg[:120],
                        sleep_sec,
                        attempt + 1,
                        max_retries
                    )
                    time.sleep(sleep_sec)
                else:
                    logger.error("Embedding request failed after %d attempts: %s", attempt + 1, err_msg)
                    raise

    def embed_documents(
        self,
        texts: List[str],
        batch_size: int = EMBEDDING_BATCH_SIZE
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of document chunks.
        Uses task_type="RETRIEVAL_DOCUMENT" and batches requests.
        """
        if not texts:
            return []

        all_embeddings: List[List[float]] = []
        total = len(texts)

        for i in range(0, total, batch_size):
            batch = texts[i : i + batch_size]
            logger.info("Embedding batch %d-%d of %d documents...", i + 1, min(i + batch_size, total), total)

            config = types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=self.output_dimensionality,
            )

            response = self._execute_with_retry(
                lambda: self.client.models.embed_content(
                    model=self.model_name,
                    contents=batch,
                    config=config
                )
            )

            if not response.embeddings:
                raise ValueError(f"No embeddings returned for batch {i}-{i + len(batch)}")

            batch_vecs = [e.values for e in response.embeddings]
            all_embeddings.extend(batch_vecs)

        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single user search query.
        Uses task_type="RETRIEVAL_QUERY".
        """
        cleaned_query = text.strip()
        if not cleaned_query:
            raise ValueError("Query text cannot be empty.")

        config = types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=self.output_dimensionality,
        )

        response = self._execute_with_retry(
            lambda: self.client.models.embed_content(
                model=self.model_name,
                contents=cleaned_query,
                config=config
            )
        )

        if not response.embeddings or not response.embeddings[0].values:
            raise ValueError(f"Failed to generate embedding for query: '{cleaned_query[:50]}...'")

        return response.embeddings[0].values
