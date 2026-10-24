"""
RAG Chain orchestration module for ShopEase.
Supports multimodal customer support inquiries (text and images),
preserves text-only backward compatibility, enforces strict grounding,
and handles human escalation.
"""

import logging
import random
import time
from typing import Any, Callable, Dict, List, Optional, Union
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from src.llm.config import (
    FALLBACK_MODELS,
    GENERATION_MODEL,
    HISTORY_TURNS,
    SIMILARITY_THRESHOLD,
    TOP_K,
    validate_api_key,
)
from src.llm.image_utils import validate_image
from src.llm.prompts import (
    QUERY_REWRITE_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    build_rag_prompt,
    build_rewrite_prompt,
    format_context,
)
from src.llm.vision import describe_image
from src.retrieval.vector_store import ShopEaseVectorStore

logger = logging.getLogger(__name__)


class SourceItem(BaseModel):
    """Reference citation item for retrieved document chunks."""
    file: str = Field(..., description="Document source filename")
    page: int = Field(default=1, description="Page number where snippet originated")
    snippet: str = Field(..., description="Short text excerpt of the retrieved chunk")
    score: float = Field(..., description="Cosine similarity score (0.0 - 1.0)")
    chunk_id: str = Field(..., description="Deterministic chunk identifier")


class RAGResponse(BaseModel):
    """Structured response from the RAG pipeline."""
    answer: str = Field(..., description="Generated customer support answer")
    sources: List[SourceItem] = Field(default_factory=list, description="List of source citations")
    confidence: float = Field(..., description="Top retrieval similarity score")
    escalate: bool = Field(..., description="True if answer requires human agent handoff")
    rewritten_query: str = Field(..., description="The search query used for retrieval")
    image_description: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured vision metadata when an image is provided"
    )


class RAGChain:
    """
    Orchestrates Retrieval-Augmented Generation for customer support questions.
    Accepts text queries as well as multimodal image inputs.
    """

    def __init__(
        self,
        vector_store: Optional[ShopEaseVectorStore] = None,
        model_name: str = GENERATION_MODEL,
        fallback_models: Optional[List[str]] = None,
        threshold: float = SIMILARITY_THRESHOLD,
        top_k: int = TOP_K,
        api_key: Optional[str] = None
    ):
        self.api_key = api_key or validate_api_key()
        self.model_name = model_name
        self.fallback_models = fallback_models if fallback_models is not None else FALLBACK_MODELS
        self.active_model = self.model_name
        self.threshold = threshold
        self.top_k = top_k
        self.vector_store = vector_store or ShopEaseVectorStore()
        self.client = genai.Client(api_key=self.api_key)

    def _generate_with_retry_and_fallback(
        self,
        contents: Union[str, List[Any]],
        config: types.GenerateContentConfig,
        max_retries: int = 5,
        initial_delay: float = 2.0
    ) -> Any:
        """Execute Gemini API generation with exponential backoff and model fallback on quota limits."""
        models_to_try = [self.active_model] + [m for m in self.fallback_models if m != self.active_model]

        for model_idx, model in enumerate(models_to_try):
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content(
                        model=model,
                        contents=contents,
                        config=config
                    )
                    self.active_model = model
                    return response
                except Exception as exc:
                    err_msg = str(exc)
                    is_quota_exhausted = "quota exceeded" in err_msg.lower() or "resource_exhausted" in err_msg.lower()
                    is_load_spike = "503" in err_msg or "overloaded" in err_msg.lower()
                    is_rate_limit = "429" in err_msg or "rate limit" in err_msg.lower()

                    if is_quota_exhausted and model_idx < len(models_to_try) - 1:
                        next_model = models_to_try[model_idx + 1]
                        logger.warning(
                            "Quota exhausted for model %s. Gracefully falling back to %s...",
                            model,
                            next_model
                        )
                        break

                    if (is_rate_limit or is_load_spike) and attempt < max_retries - 1:
                        sleep_sec = (initial_delay * (2 ** attempt)) + random.uniform(0.5, 1.5)
                        logger.warning(
                            "Model %s rate limited or busy (%s). Retrying in %.1fs (attempt %d/%d)...",
                            model,
                            err_msg[:120],
                            sleep_sec,
                            attempt + 1,
                            max_retries
                        )
                        time.sleep(sleep_sec)
                    else:
                        if model_idx == len(models_to_try) - 1:
                            logger.error("Generation failed across all models. Last error: %s", err_msg)
                            raise
                        break

    def rewrite_query(self, query: str, history: List[Dict[str, str]]) -> str:
        """
        Rewrite a conversational follow-up into a standalone question.
        Optimized: If history is empty, skips the LLM call entirely.
        """
        if not history:
            return query.strip()

        recent_history = history[-HISTORY_TURNS:]
        prompt_content = build_rewrite_prompt(recent_history, query)

        logger.info("Rewriting query with conversation history (%d turns)...", len(recent_history))

        config = types.GenerateContentConfig(
            system_instruction=QUERY_REWRITE_SYSTEM_PROMPT,
            temperature=0.0,
            max_output_tokens=500
        )

        response = self._generate_with_retry_and_fallback(
            contents=prompt_content,
            config=config
        )

        rewritten = response.text.strip() if response.text else query.strip()
        logger.info("Original: '%s' -> Rewritten: '%s'", query, rewritten)
        return rewritten

    def answer(
        self,
        query: str,
        history: Optional[List[Dict[str, str]]] = None,
        image: Optional[bytes] = None,
        image_filename: Optional[str] = None
    ) -> RAGResponse:
        """
        End-to-end RAG answer pipeline supporting text and multimodal inputs:
        1. If image provided: validates bytes, performs vision analysis
        2. Resolves conversational search query (rewritten if history exists)
        3. Enriches retrieval query with visual metadata (error codes, product hints)
        4. Queries vector store for relevant support chunks
        5. Calls Gemini (passing ORIGINAL image + context if image present)
        6. Evaluates confidence & human escalation
        """
        history = history or []
        cleaned_query = query.strip()

        vision_data: Optional[Dict[str, Any]] = None
        mime_type: Optional[str] = None
        retrieval_query = cleaned_query

        # Step 1: Multimodal Vision Analysis (if image provided)
        if image is not None:
            filename = image_filename or "upload.png"
            mime_type = validate_image(image, filename)
            logger.info("Validated image '%s' with MIME type %s", filename, mime_type)
            vision_data = describe_image(image, mime_type, user_text=cleaned_query, client=self.client)

        # Step 2: Query Rewriting (skipped if no history)
        search_query = self.rewrite_query(cleaned_query, history)

        # Step 3: Query Enrichment with visual features (high-signal tokens only)
        if vision_data:
            extracted_text = vision_data.get("extracted_text", "").strip()
            product_hint = (vision_data.get("product_hint") or "").strip()
            issue_type = vision_data.get("issue_type", "")

            enrichment_tokens = []
            if extracted_text:
                enrichment_tokens.append(extracted_text)
            if product_hint and product_hint.lower() not in search_query.lower():
                enrichment_tokens.append(product_hint)

            if enrichment_tokens:
                retrieval_query = f"{search_query} {' '.join(enrichment_tokens)}".strip()
            elif vision_data.get("description"):
                retrieval_query = f"{search_query} {vision_data.get('description', '')}".strip()
            else:
                retrieval_query = search_query

            logger.info("Enriched multimodal retrieval query: '%s'", retrieval_query)
        else:
            retrieval_query = search_query

        # Step 4: Vector Retrieval
        chunks = self.vector_store.search(retrieval_query, top_k=self.top_k)

        top_score = chunks[0]["score"] if chunks else 0.0
        confidence = round(top_score, 4)

        sources: List[SourceItem] = []
        for c in chunks:
            meta = c.get("metadata", {})
            sources.append(SourceItem(
                file=meta.get("source", "unknown"),
                page=meta.get("page", 1),
                snippet=c.get("text", "")[:180].replace("\n", " "),
                score=c.get("score", 0.0),
                chunk_id=meta.get("chunk_id", "n/a")
            ))

        # Step 5: Grounded Generation (passes ORIGINAL image if present)
        context_str = format_context(chunks)
        user_prompt = build_rag_prompt(search_query, context_str)

        if image is not None and mime_type is not None:
            # Multimodal payload: [Original Image, Text Prompt with Context]
            image_part = types.Part.from_bytes(data=image, mime_type=mime_type)
            contents_payload: List[Any] = [image_part, user_prompt]
        else:
            # Text-only payload
            contents_payload = user_prompt

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
            max_output_tokens=700
        )

        response = self._generate_with_retry_and_fallback(
            contents=contents_payload,
            config=config
        )

        answer_text = response.text.strip() if response.text else ""

        # Step 6: Escalation Evaluation
        lack_of_info = "i don't have that information" in answer_text.lower()
        low_confidence = confidence < self.threshold
        unrelated_image = bool(vision_data and vision_data.get("issue_type") == "other" and low_confidence)
        escalate = low_confidence or lack_of_info or unrelated_image

        if escalate:
            logger.info("Human escalation triggered for query '%s' (Confidence: %.4f)", cleaned_query, confidence)

        return RAGResponse(
            answer=answer_text,
            sources=sources,
            confidence=confidence,
            escalate=escalate,
            rewritten_query=search_query,
            image_description=vision_data
        )
