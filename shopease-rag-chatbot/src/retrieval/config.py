"""
Configuration module for retrieval, embeddings, and ChromaDB vector store.
Loads GEMINI_API_KEY securely from .env and exposes standard configuration constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

# Load environment variables from .env
load_dotenv(dotenv_path=ENV_PATH)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
if not GEMINI_API_KEY:
    try:
        import streamlit as st
        GEMINI_API_KEY = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
        if GEMINI_API_KEY:
            os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
    except Exception:
        pass

# Validations
def validate_api_key() -> str:
    """Validate that GEMINI_API_KEY exists and is not the default placeholder."""
    global GEMINI_API_KEY
    if not GEMINI_API_KEY:
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
        if not GEMINI_API_KEY:
            try:
                import streamlit as st
                GEMINI_API_KEY = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
                if GEMINI_API_KEY:
                    os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
            except Exception:
                pass

    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_key_here":
        raise ValueError(
            "GEMINI_API_KEY is not configured or still set to 'your_key_here'.\n"
            "Please configure your valid Google Gemini API key in .env (for local) or Streamlit Secrets (for cloud deployment)."
        )
    return GEMINI_API_KEY


# Retrieval & Embedding constants
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSION = 768
CHROMA_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "shopease_docs"
EMBEDDING_BATCH_SIZE = 20
PROCESSED_CHUNKS_PATH = BASE_DIR / "data" / "processed" / "chunks.json"
