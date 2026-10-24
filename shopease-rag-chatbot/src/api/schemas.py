"""
Pydantic response and request schemas for ShopEase FastAPI backend.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


from src.llm.rag_chain import SourceItem


class ChatResponse(BaseModel):
    """Response returned by the /chat endpoint."""
    answer: str = Field(..., description="Generated customer support response")
    sources: List[SourceItem] = Field(default_factory=list, description="List of source citations")
    confidence: float = Field(..., description="Top retrieval similarity score")
    escalate: bool = Field(..., description="True if answer requires human agent handoff")
    rewritten_query: str = Field(..., description="The query used for document search")
    image_description: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured vision metadata when an image was provided"
    )
    session_id: str = Field(..., description="Conversation session identifier")


class Turn(BaseModel):
    """Single conversation turn."""
    role: str = Field(..., description="Role of the sender ('user' or 'assistant')")
    content: str = Field(..., description="Text content of the message")
    created_at: Optional[str] = Field(default=None, description="Timestamp of the turn")


class HistoryResponse(BaseModel):
    """Response returned by the /history/{session_id} endpoint."""
    session_id: str = Field(..., description="Conversation session identifier")
    history: List[Turn] = Field(default_factory=list, description="Chronological conversation turns")


class IngestResponse(BaseModel):
    """Response returned by the /ingest endpoint."""
    filename: str = Field(..., description="Sanitized filename of the ingested file")
    chunks_added: int = Field(..., description="Number of new chunks added to the vector store")
    total_chunks: int = Field(..., description="Total chunks currently in the vector store")
    message: str = Field(..., description="Status summary of the ingestion operation")


class HealthResponse(BaseModel):
    """Response returned by the /health endpoint. Never returns the API key."""
    status: str = Field(default="ok", description="Service health status")
    vector_store_count: int = Field(..., description="Total document chunks in ChromaDB")
    api_key_configured: bool = Field(..., description="Whether GEMINI_API_KEY is configured")
    model: Optional[str] = Field(default=None, description="Primary active generation model name")
