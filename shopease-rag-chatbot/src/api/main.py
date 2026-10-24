"""
FastAPI REST application for ShopEase Multimodal RAG Assistant.
Features:
- Single RAGChain instance managed via lifespan context
- Endpoints: /chat, /ingest, /health, /history/{session_id}
- SQLite-backed conversation memory (text-only)
- Deep image byte validation and path-traversal sanitization
- CORS support for Streamlit (localhost:8501)
- Request logging middleware and global exception sanitization
"""

from contextlib import asynccontextmanager
import json
import logging
import os
from pathlib import Path
import re
import time
from typing import Any, Dict, List, Optional
import uuid

from fastapi import FastAPI, File, Form, HTTPException, Request, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from src.api.schemas import (
    ChatResponse,
    HealthResponse,
    HistoryResponse,
    IngestResponse,
    SourceItem,
    Turn,
)
from src.api.session_store import (
    add_turn,
    clear_session,
    get_history,
    get_history_detailed,
)
from src.ingestion.cleaner import clean_text
from src.ingestion.chunker import RecursiveCharacterChunker
from src.ingestion.loaders import LOADER_MAPPING, load_document
from src.llm.image_utils import ImageValidationError, validate_image
from src.llm.rag_chain import RAGChain

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("src.api.main")

# Constants
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_CHUNKS_FILE = BASE_DIR / "data" / "processed" / "chunks.json"
MAX_INGEST_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_INGEST_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager:
    Initializes the RAGChain singleton ONCE during server startup.
    Avoids reconnecting to vector stores or reloading configs per request.
    """
    logger.info("Initializing RAGChain singleton in lifespan...")
    try:
        app.state.rag_chain = RAGChain()
        logger.info("RAGChain singleton initialized successfully.")

        # Auto-populate vector store if empty (e.g. fresh cloud deployment)
        try:
            if app.state.rag_chain.vector_store.get_count() == 0:
                logger.info("Vector store is empty. Auto-indexing baseline documents...")
                from src.ingestion.run import run_ingestion
                from src.retrieval.config import PROCESSED_CHUNKS_PATH
                if not PROCESSED_CHUNKS_PATH.exists():
                    run_ingestion()
                if PROCESSED_CHUNKS_PATH.exists():
                    with open(PROCESSED_CHUNKS_PATH, "r", encoding="utf-8") as f:
                        chunks = json.load(f)
                    if chunks:
                        app.state.rag_chain.vector_store.add_documents(chunks)
                        logger.info("Auto-indexing complete. Vectors count: %d", app.state.rag_chain.vector_store.get_count())
        except Exception as auto_idx_err:
            logger.warning("Auto-indexing skipped or failed: %s", auto_idx_err)
    except Exception as exc:
        logger.warning(
            "RAGChain could not be initialized during startup (%s). "
            "May be initialized lazily or replaced by a test mock.",
            exc
        )
        app.state.rag_chain = None

    yield

    logger.info("Shutting down ShopEase API service...")


app = FastAPI(
    title="ShopEase Multimodal RAG API",
    description="Customer support intelligence platform powered by Gemini and ChromaDB.",
    version="1.0.0",
    lifespan=lifespan
)

# ---------------------------------------------------------------------------
# CORS Middleware (Supports Streamlit at localhost:8501)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request Logging Middleware (Method, Path, Status, Latency)
# ---------------------------------------------------------------------------
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    try:
        response: Response = await call_next(request)
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(
            "%s %s -> %d (%.2f ms)",
            request.method,
            request.url.path,
            response.status_code,
            latency_ms
        )
        response.headers["X-Process-Time-Ms"] = f"{latency_ms:.2f}"
        return response
    except Exception as exc:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        logger.error(
            "%s %s -> Exception: %s (%.2f ms)",
            request.method,
            request.url.path,
            exc,
            latency_ms,
            exc_info=True
        )
        raise exc


# ---------------------------------------------------------------------------
# Exception Handlers (Clean JSON, No Client Stack Traces)
# ---------------------------------------------------------------------------
@app.exception_handler(ImageValidationError)
async def image_validation_exception_handler(request: Request, exc: ImageValidationError):
    """Convert custom image validation errors to clean HTTP 400 JSON responses."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global fallback returning sanitized JSON without leaking internal Python stack traces."""
    # If it's already an HTTPException, preserve its status and detail
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )

    logger.error("Unhandled internal server exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."}
    )


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------
@app.get("/", include_in_schema=False)
async def root():
    """Redirect root path to interactive Swagger documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthResponse)
async def health(request: Request):
    """
    Reports vector store chunk count and API key status.
    Security: The API key value itself is NEVER revealed or logged.
    """
    rag_chain = getattr(request.app.state, "rag_chain", None)
    chunk_count = 0
    active_model = None

    if rag_chain and hasattr(rag_chain, "vector_store") and rag_chain.vector_store is not None:
        try:
            chunk_count = rag_chain.vector_store.get_count()
        except Exception as exc:
            logger.warning("Error fetching chunk count from rag_chain: %s", exc)
        active_model = getattr(rag_chain, "active_model", getattr(rag_chain, "model_name", None))
    else:
        try:
            from src.retrieval.vector_store import ShopEaseVectorStore
            store = ShopEaseVectorStore()
            chunk_count = store.get_count()
        except Exception:
            chunk_count = 0

    api_key_configured = bool(getattr(rag_chain, "api_key", False))
    if not api_key_configured:
        try:
            from src.llm.config import validate_api_key
            key = validate_api_key()
            api_key_configured = bool(key and str(key).strip())
        except Exception:
            api_key_configured = False

    return HealthResponse(
        status="ok",
        vector_store_count=chunk_count,
        api_key_configured=api_key_configured,
        model=active_model
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(
    message: str = Form(..., description="Customer question or issue message"),
    image: Optional[UploadFile] = File(None, description="Optional image file (PNG, JPG, WEBP)"),
    session_id: Optional[str] = Form(None, description="Conversation session ID"),
    request: Request = None,
):
    """
    Conversational support endpoint.
    Supports text queries as well as multimodal image attachments.
    Maintains conversation turns in SQLite.
    """
    # 1. Resolve or create session ID
    active_session_id = (session_id or "").strip()
    if not active_session_id:
        active_session_id = str(uuid.uuid4())

    # 2. Process and validate image if present
    image_bytes: Optional[bytes] = None
    image_filename: Optional[str] = None

    if image is not None:
        content = await image.read()
        if content and len(content) > 0:
            image_filename = image.filename or "upload.png"
            # Validate image with Pillow - raises ImageValidationError on invalid bytes/format
            validate_image(content, image_filename)
            image_bytes = content

    # 3. Retrieve conversation history
    history = get_history(active_session_id, last_n=5)

    # 4. Resolve RAGChain instance
    rag_chain = getattr(request.app.state, "rag_chain", None)
    if rag_chain is None:
        rag_chain = RAGChain()
        request.app.state.rag_chain = rag_chain

    # 5. Execute RAG pipeline
    rag_result = rag_chain.answer(
        query=message,
        history=history,
        image=image_bytes,
        image_filename=image_filename
    )

    # 6. Save textual turns to session store (never image bytes)
    add_turn(active_session_id, role="user", content=message)
    add_turn(active_session_id, role="assistant", content=rag_result.answer)

    # 7. Format sources safely
    formatted_sources: List[SourceItem] = []
    for s in rag_result.sources:
        if isinstance(s, dict):
            formatted_sources.append(SourceItem(
                file=s.get("file", "unknown"),
                page=s.get("page", 1),
                snippet=s.get("snippet", ""),
                score=s.get("score", 0.0),
                chunk_id=s.get("chunk_id", "n/a")
            ))
        else:
            formatted_sources.append(SourceItem(
                file=getattr(s, "file", "unknown"),
                page=getattr(s, "page", 1),
                snippet=getattr(s, "snippet", ""),
                score=getattr(s, "score", 0.0),
                chunk_id=getattr(s, "chunk_id", "n/a")
            ))

    return ChatResponse(
        answer=rag_result.answer,
        sources=formatted_sources,
        confidence=rag_result.confidence,
        escalate=rag_result.escalate,
        rewritten_query=rag_result.rewritten_query,
        image_description=rag_result.image_description,
        session_id=active_session_id
    )


@app.post("/ingest", response_model=IngestResponse)
async def ingest(
    file: UploadFile = File(..., description="Document to ingest (PDF, DOCX, TXT, MD max 10MB)"),
    request: Request = None,
):
    """
    Upload and index a new support document.
    - Sanitizes filename against path traversal attacks (e.g. ../../evil.txt).
    - Enforces 10 MB maximum size.
    - Saves document to data/raw.
    - Runs cleaning, chunking, and ChromaDB vector indexing.
    """
    raw_filename = file.filename or "upload.txt"

    # Path traversal protection: strip all directory paths, null bytes, and parent references
    base_name = os.path.basename(raw_filename)
    safe_name = Path(base_name).name
    safe_name = re.sub(r"[\x00/\\:]", "", safe_name).strip()
    safe_name = safe_name.lstrip(".")

    if not safe_name or safe_name in {".", ".."}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename supplied."
        )

    # Validate file extension
    ext = Path(safe_name).suffix.lower()
    if ext not in ALLOWED_INGEST_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed types: {', '.join(sorted(ALLOWED_INGEST_EXTENSIONS))}"
        )

    # Read and validate file size
    content = await file.read()
    if len(content) > MAX_INGEST_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed limit of {MAX_INGEST_SIZE_BYTES // (1024*1024)} MB."
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    # Secure destination path verification
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    destination_path = (RAW_DIR / safe_name).resolve()

    if not str(destination_path).startswith(str(RAW_DIR.resolve())):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path traversal violation detected."
        )

    destination_path.write_bytes(content)
    logger.info("Saved ingested file to %s (%d bytes)", destination_path, len(content))

    # Ingestion & chunking pipeline
    try:
        raw_docs = load_document(destination_path)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse document: {exc}"
        )

    cleaned_docs = []
    for doc in raw_docs:
        cleaned_text = clean_text(doc.get("text", ""))
        if cleaned_text:
            cleaned_docs.append({
                "text": cleaned_text,
                "metadata": doc.get("metadata", {})
            })

    chunker = RecursiveCharacterChunker(chunk_size=800, chunk_overlap=150)
    new_chunks = chunker.split_documents(cleaned_docs)

    if not new_chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No readable textual content could be extracted from this document."
        )

    # Update data/processed/chunks.json
    PROCESSED_CHUNKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing_chunks: List[Dict[str, Any]] = []
    if PROCESSED_CHUNKS_FILE.exists():
        try:
            with open(PROCESSED_CHUNKS_FILE, "r", encoding="utf-8") as f:
                existing_chunks = json.load(f)
        except Exception:
            existing_chunks = []

    existing_chunk_ids = {
        c.get("metadata", {}).get("chunk_id")
        for c in existing_chunks
        if c.get("metadata", {}).get("chunk_id")
    }
    chunks_to_append = [
        c for c in new_chunks
        if c.get("metadata", {}).get("chunk_id") not in existing_chunk_ids
    ]
    all_chunks = existing_chunks + chunks_to_append

    with open(PROCESSED_CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    # Index into vector store
    rag_chain = getattr(request.app.state, "rag_chain", None)
    if rag_chain and hasattr(rag_chain, "vector_store") and rag_chain.vector_store is not None:
        chunks_added = rag_chain.vector_store.add_documents(new_chunks)
        total_chunks = rag_chain.vector_store.get_count()
    else:
        from src.retrieval.vector_store import ShopEaseVectorStore
        store = ShopEaseVectorStore()
        chunks_added = store.add_documents(new_chunks)
        total_chunks = store.get_count()

    return IngestResponse(
        filename=safe_name,
        chunks_added=chunks_added,
        total_chunks=total_chunks,
        message=f"Successfully indexed {chunks_added} chunk(s) from '{safe_name}'."
    )


@app.get("/history/{session_id}", response_model=HistoryResponse)
async def get_session_history_endpoint(session_id: str):
    """Retrieve full conversation history for a given session_id."""
    raw_history = get_history_detailed(session_id, last_n=100)
    turns = [
        Turn(
            role=h["role"],
            content=h["content"],
            created_at=h.get("created_at")
        )
        for h in raw_history
    ]
    return HistoryResponse(
        session_id=session_id,
        history=turns
    )


@app.delete("/history/{session_id}")
async def delete_session_history_endpoint(session_id: str):
    """Clear conversation history for a given session_id."""
    cleared = clear_session(session_id)
    return {
        "session_id": session_id,
        "cleared": cleared,
        "message": f"Conversation history for session '{session_id}' has been cleared."
    }
