"""
Integration test suite for Multimodal Image Support in ShopEase RAG pipeline.
Covers vision text extraction, multimodal document retrieval, and human escalation.

Runs with:
pytest tests/test_multimodal.py -v -m integration
"""

import io
from pathlib import Path
import pytest
from PIL import Image

from src.llm.rag_chain import RAGChain

ASSETS_DIR = Path(__file__).resolve().parent / "assets"


@pytest.fixture(scope="module")
def rag_chain():
    """Shared RAGChain instance for multimodal testing."""
    return RAGChain()


@pytest.mark.integration
def test_error_screenshot_flow(rag_chain):
    """Verify error screenshot extracts ERR_PAY_402 and retrieves troubleshooting guide."""
    img_path = ASSETS_DIR / "error_screenshot.png"
    assert img_path.exists(), f"Asset missing: {img_path}"

    img_bytes = img_path.read_bytes()
    response = rag_chain.answer(
        query="Why did my checkout payment fail?",
        image=img_bytes,
        image_filename=img_path.name
    )

    assert response.image_description is not None, "Image description should be populated"
    vis = response.image_description
    assert "ERR_PAY_402" in vis.get("extracted_text", ""), (
        f"Expected ERR_PAY_402 in extracted text: {vis.get('extracted_text')}"
    )

    # Top source should be troubleshooting_guide.docx
    top_sources = [s.file for s in response.sources]
    assert "troubleshooting_guide.docx" in top_sources, (
        f"Expected troubleshooting_guide.docx in sources: {top_sources}"
    )
    assert response.escalate is False, "Legitimate error code question should not escalate"
    assert "3d secure" in response.answer.lower() or "timeout" in response.answer.lower()


@pytest.mark.integration
def test_damaged_product_flow(rag_chain):
    """Verify photo of damaged item retrieves damage policy SLA and instructions."""
    img_path = ASSETS_DIR / "damaged_product.jpg"
    assert img_path.exists(), f"Asset missing: {img_path}"

    img_bytes = img_path.read_bytes()
    response = rag_chain.answer(
        query="My band arrived like this in the box, what can I do?",
        image=img_bytes,
        image_filename=img_path.name
    )

    assert response.image_description is not None
    vis = response.image_description
    assert vis.get("issue_type") in ["damaged_product", "error_screenshot"]

    answer_lower = response.answer.lower()
    assert ("48 hour" in answer_lower or "replacement" in answer_lower or "photo" in answer_lower or "return" in answer_lower), (
        f"Expected damage resolution steps in answer: {response.answer}"
    )


@pytest.mark.integration
def test_unrelated_image_triggers_escalation(rag_chain):
    """Verify an unrelated non-support image triggers human escalation."""
    # Create simple green square image (unrelated to e-commerce support)
    unrelated_img = Image.new("RGB", (200, 200), color=(34, 197, 94))
    buf = io.BytesIO()
    unrelated_img.save(buf, format="PNG")
    unrelated_bytes = buf.getvalue()

    response = rag_chain.answer(
        query="What is the meaning of life?",
        image=unrelated_bytes,
        image_filename="green_box.png"
    )

    assert response.escalate is True, (
        f"Unrelated query and image must trigger escalate=True. Got escalate={response.escalate}"
    )
