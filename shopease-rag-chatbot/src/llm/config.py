"""
Configuration module for LLM generation and RAG chain.
"""

from src.retrieval.config import GEMINI_API_KEY, validate_api_key

# Fast, verified text generation models for ShopEase RAG
GENERATION_MODEL = "gemini-3.5-flash"
FALLBACK_MODELS = ["gemini-3.8-flash", "gemini-3.1-flash-lite"]

# RAG parameters
TOP_K = 4
SIMILARITY_THRESHOLD = 0.62  # Tuned via scripts/tune_threshold.py (clear separation at 0.62)
HISTORY_TURNS = 5
