"""
Unit tests for RecursiveCharacterChunker.
Verifies chunk size, overlap, metadata preservation, chunk ID uniqueness, and edge cases.
"""

import pytest
from src.ingestion.chunker import RecursiveCharacterChunker


def test_chunk_size_respected():
    """Verify generated chunks do not exceed chunk_size."""
    chunker = RecursiveCharacterChunker(chunk_size=200, chunk_overlap=30)
    sample_text = (
        "ShopEase offers a 30-day standard return window for all customers.\n\n"
        "Items must be in brand-new condition with original packaging, tags, and accessories intact.\n\n"
        "Customers must report transit damage within 48 hours of confirmed delivery.\n\n"
        "Refunds are processed within 3 to 5 business days back to the original payment method."
    )
    chunks = chunker.split_text(sample_text)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 200


def test_chunk_overlap():
    """Verify consecutive chunks share overlapping tokens."""
    chunker = RecursiveCharacterChunker(chunk_size=150, chunk_overlap=40)
    sample_text = (
        "The ShopEase SmartBand X1 features an AMOLED touchscreen display. "
        "It supports continuous heart rate monitoring, SpO2 tracking, and sleep stages. "
        "Battery life lasts up to 12 days on a single charge."
    )
    chunks = chunker.split_text(sample_text)
    assert len(chunks) >= 2
    # Check that chunk 2 shares common substring or words from chunk 1
    chunk1_words = set(chunks[0].split())
    chunk2_words = set(chunks[1].split())
    common_words = chunk1_words.intersection(chunk2_words)
    assert len(common_words) > 0


def test_metadata_preserved():
    """Verify document metadata is preserved and augmented in chunk objects."""
    chunker = RecursiveCharacterChunker(chunk_size=300, chunk_overlap=50)
    doc = {
        "text": "Paragraph 1 about return policies.\n\nParagraph 2 about refund timeframes.",
        "metadata": {
            "source": "return_policy.pdf",
            "page": 2,
            "category": "legal"
        }
    }
    chunks = chunker.split_document(doc)
    assert len(chunks) >= 1
    for chunk in chunks:
        meta = chunk["metadata"]
        assert meta["source"] == "return_policy.pdf"
        assert meta["page"] == 2
        assert meta["category"] == "legal"
        assert "chunk_id" in meta
        assert "chunk_index" in meta
        assert "char_length" in meta
        assert meta["char_length"] == len(chunk["text"])


def test_chunk_ids_unique_and_deterministic():
    """Verify chunk IDs are strictly unique, deterministic, and follow naming convention."""
    chunker = RecursiveCharacterChunker(chunk_size=120, chunk_overlap=20)
    docs = [
        {
            "text": "Page one paragraph one.\n\nPage one paragraph two.\n\nPage one paragraph three.",
            "metadata": {"source": "FAQ.md", "page": 1}
        },
        {
            "text": "Page two paragraph one.\n\nPage two paragraph two.",
            "metadata": {"source": "FAQ.md", "page": 2}
        }
    ]
    chunks1 = chunker.split_documents(docs)
    chunks2 = chunker.split_documents(docs)

    # Determinism
    ids1 = [c["metadata"]["chunk_id"] for c in chunks1]
    ids2 = [c["metadata"]["chunk_id"] for c in chunks2]
    assert ids1 == ids2

    # Uniqueness across whole set
    assert len(ids1) == len(set(ids1))

    # Correct naming pattern
    for cid in ids1:
        assert cid.startswith("FAQ.md::p")
        assert "::c" in cid


def test_empty_and_whitespace_handling():
    """Verify empty or whitespace-only texts return empty chunk lists."""
    chunker = RecursiveCharacterChunker(chunk_size=500, chunk_overlap=50)
    assert chunker.split_text("") == []
    assert chunker.split_text("   \n\t\n  ") == []

    doc = {"text": "   ", "metadata": {"source": "empty.txt", "page": 1}}
    assert chunker.split_document(doc) == []


def test_long_unbroken_text():
    """Verify very long unbroken string without separators is sliced safely."""
    chunker = RecursiveCharacterChunker(chunk_size=100, chunk_overlap=20)
    unbroken = "A" * 350
    chunks = chunker.split_text(unbroken)
    assert len(chunks) >= 4
    for chunk in chunks:
        assert len(chunk) <= 100


def test_invalid_parameters():
    """Verify chunk_overlap >= chunk_size raises ValueError."""
    with pytest.raises(ValueError):
        RecursiveCharacterChunker(chunk_size=100, chunk_overlap=100)
    with pytest.raises(ValueError):
        RecursiveCharacterChunker(chunk_size=100, chunk_overlap=150)
