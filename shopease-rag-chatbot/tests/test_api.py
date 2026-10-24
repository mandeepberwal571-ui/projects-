"""
API Test Suite for ShopEase FastAPI Backend.
Uses FastAPI TestClient and a MOCKED RAGChain for fast, zero-quota unit testing.
Includes 1 marked integration test using the live RAGChain.
"""

import io
from pathlib import Path
from unittest.mock import MagicMock, patch
from PIL import Image
import pytest
from fastapi.testclient import TestClient

from src.api.main import BASE_DIR, RAW_DIR, app
from src.api.schemas import SourceItem
from src.api.session_store import clear_session, get_history
from src.llm.rag_chain import RAGResponse


def _create_test_image(format_name: str = "PNG") -> bytes:
    """Create a minimal valid in-memory image."""
    img = Image.new("RGB", (64, 64), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format=format_name)
    return buf.getvalue()


@pytest.fixture
def mock_chain():
    """Create a fully mocked RAGChain instance."""
    chain = MagicMock()
    chain.model_name = "gemini-3.5-flash"
    chain.active_model = "gemini-3.5-flash"

    # Mock vector store
    store = MagicMock()
    store.get_count.return_value = 68
    store.add_documents.return_value = 2
    chain.vector_store = store

    # Mock default answer
    chain.answer.return_value = RAGResponse(
        answer="ShopEase allows returns within 30 days of delivery.",
        sources=[
            SourceItem(
                file="return_policy.pdf",
                page=1,
                snippet="Customers may return undamaged items within 30 days.",
                score=0.88,
                chunk_id="chunk_ret_01"
            )
        ],
        confidence=0.88,
        escalate=False,
        rewritten_query="return policy window",
        image_description=None
    )
    return chain


@pytest.fixture
def client(mock_chain):
    """FastAPI TestClient fixture with mocked RAGChain."""
    with patch("src.api.main.RAGChain", return_value=mock_chain):
        with TestClient(app) as test_client:
            app.state.rag_chain = mock_chain
            yield test_client


def test_health_endpoint(client, mock_chain):
    """Verify /health reports status, chunk count 68, and NEVER exposes the API key."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["vector_store_count"] == 68
    assert isinstance(data["api_key_configured"], bool)

    # Security check: ensure API key value is never present in response text
    assert "AIzaSy" not in response.text
    assert "GEMINI_API_KEY" not in response.text


def test_chat_text_query(client, mock_chain):
    """Verify text query to /chat returns ChatResponse and persists turn to session store."""
    session_id = "test_text_session_101"
    clear_session(session_id)

    response = client.post(
        "/chat",
        data={
            "message": "What is your return policy?",
            "session_id": session_id
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "30 days" in data["answer"]
    assert data["session_id"] == session_id
    assert data["escalate"] is False
    assert data["confidence"] == 0.88
    assert len(data["sources"]) == 1
    assert data["sources"][0]["file"] == "return_policy.pdf"

    # Verify session store recorded the turn
    history = get_history(session_id, last_n=5)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "What is your return policy?"
    assert history[1]["role"] == "assistant"
    assert "30 days" in history[1]["content"]

    clear_session(session_id)


def test_chat_auto_generates_session_id_when_missing(client, mock_chain):
    """Verify /chat auto-generates a UUID session_id if none is provided."""
    response = client.post(
        "/chat",
        data={"message": "Do you deliver to Canada?"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"]
    assert len(data["session_id"]) >= 10


def test_chat_invalid_image_returns_400(client):
    """Verify invalid image bytes trigger HTTP 400 with a clear error message."""
    fake_bytes = b"not-a-real-image-corrupt-data"

    response = client.post(
        "/chat",
        data={"message": "Can you check this error?"},
        files={"image": ("corrupted.png", fake_bytes, "image/png")}
    )

    assert response.status_code == 400
    detail = response.json().get("detail", "")
    assert "Invalid image" in detail or "corrupted" in detail or "Unsupported" in detail


def test_chat_with_valid_image(client, mock_chain):
    """Verify /chat with a valid image calls vision and returns image_description."""
    png_bytes = _create_test_image("PNG")
    session_id = "test_image_session_202"

    mock_chain.answer.return_value = RAGResponse(
        answer="I see error code ERR_PAY_402. Please verify 3D Secure authentication.",
        sources=[
            SourceItem(
                file="troubleshooting_guide.docx",
                page=1,
                snippet="ERR_PAY_402 indicates 3D Secure authentication failure.",
                score=0.82,
                chunk_id="chunk_err_402"
            )
        ],
        confidence=0.82,
        escalate=False,
        rewritten_query="ERR_PAY_402 3D Secure",
        image_description={
            "issue_type": "error_screen",
            "extracted_text": "ERR_PAY_402",
            "product_hint": None
        }
    )

    response = client.post(
        "/chat",
        data={
            "message": "Why is my checkout failing?",
            "session_id": session_id
        },
        files={"image": ("error.png", png_bytes, "image/png")}
    )

    assert response.status_code == 200
    data = response.json()

    assert "ERR_PAY_402" in data["answer"]
    assert data["image_description"] is not None
    assert data["image_description"]["extracted_text"] == "ERR_PAY_402"
    assert data["sources"][0]["file"] == "troubleshooting_guide.docx"

    clear_session(session_id)


def test_history_endpoints_lifecycle(client):
    """Verify GET and DELETE /history/{session_id} endpoints."""
    session_id = "test_hist_crud_303"
    clear_session(session_id)

    # Initially empty
    res1 = client.get(f"/history/{session_id}")
    assert res1.status_code == 200
    assert res1.json()["history"] == []

    # Send a chat message
    client.post(
        "/chat",
        data={"message": "First message", "session_id": session_id}
    )

    # Check history is populated
    res2 = client.get(f"/history/{session_id}")
    assert res2.status_code == 200
    history = res2.json()["history"]
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "First message"

    # Delete history
    res3 = client.delete(f"/history/{session_id}")
    assert res3.status_code == 200
    assert res3.json()["cleared"] is True

    # Check history is empty again
    res4 = client.get(f"/history/{session_id}")
    assert res4.status_code == 200
    assert res4.json()["history"] == []


def test_ingest_path_traversal_sanitization(client, tmp_path):
    """
    Verify path traversal filenames like '../../evil.txt' are safely sanitized
    and contained strictly inside data/raw/.
    """
    traversal_filename = "../../evil_test_doc.txt"
    file_content = b"ShopEase Return Policy addendum: 45 days window for holidays.\n"

    tmp_chunks = tmp_path / "chunks.json"
    with patch("src.api.main.PROCESSED_CHUNKS_FILE", tmp_chunks):
        response = client.post(
            "/ingest",
            files={"file": (traversal_filename, file_content, "text/plain")}
        )

    assert response.status_code == 200
    data = response.json()

    # Filename must be sanitized
    assert ".." not in data["filename"]
    assert data["filename"] == "evil_test_doc.txt"

    # Assert the file NEVER escaped to project root or parent dir
    escaped_path = BASE_DIR / "evil_test_doc.txt"
    assert not escaped_path.exists(), "File escaped path traversal filter into root directory!"

    # Clean up test artifact from data/raw/
    raw_saved = RAW_DIR / "evil_test_doc.txt"
    if raw_saved.exists():
        raw_saved.unlink()


def test_ingest_wrong_file_type_rejected(client):
    """Verify uploading an unsupported file type returns HTTP 400."""
    response = client.post(
        "/ingest",
        files={"file": ("malicious_script.exe", b"binary content", "application/octet-stream")}
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_ingest_oversized_file_rejected(client):
    """Verify uploading a file > 10 MB returns HTTP 400."""
    large_content = b"A" * (10 * 1024 * 1024 + 1024)

    response = client.post(
        "/ingest",
        files={"file": ("oversized.txt", large_content, "text/plain")}
    )

    assert response.status_code == 400
    assert "exceeds maximum allowed limit" in response.json()["detail"]


@pytest.mark.integration
def test_real_chain_integration():
    """
    Single integration test using the LIVE RAGChain (with real vector store & API).
    Ensures that FastAPI routes work seamlessly with the production pipeline.
    """
    with TestClient(app) as live_client:
        response = live_client.post(
            "/chat",
            data={"message": "How many days do I have to return a product?"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["answer"]
        assert "30" in data["answer"]
        assert data["escalate"] is False
        assert len(data["sources"]) > 0
        top_files = [s["file"] for s in data["sources"]]
        assert any("return_policy" in f or "FAQ" in f for f in top_files)
