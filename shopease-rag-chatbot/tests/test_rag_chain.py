"""
Integration test suite for ShopEase RAG pipeline.
Covers in-domain question answering, citation verification, and out-of-domain human escalation.

Runs with:
pytest tests/test_rag_chain.py -v -m integration
"""

import pytest
from src.llm.rag_chain import RAGChain


@pytest.fixture(scope="module")
def rag_chain():
    """Shared RAGChain instance for integration testing."""
    return RAGChain()


@pytest.mark.integration
@pytest.mark.parametrize("query,expected_keyword", [
    ("How many days do I have to return a product?", "30"),
    ("What does error code ERR_PAY_402 mean?", "3D Secure"),
    ("How do I factory reset my SmartBand X1?", "reset"),
    ("What are the shipping costs for standard delivery?", "4.99"),
    ("What are the customer voice phone support operating hours?", "EST"),
])
def test_in_domain_queries(rag_chain, query, expected_keyword):
    """Verify in-domain questions are answered with sources and escalate is False."""
    response = rag_chain.answer(query)

    assert response.answer, f"Answer should not be empty for query: {query}"
    assert len(response.sources) > 0, "Sources should not be empty"
    assert response.confidence >= 0.50, f"Confidence should be reasonable, got: {response.confidence}"
    assert response.escalate is False, f"In-domain query '{query}' should not escalate. (Answer: {response.answer})"
    assert expected_keyword.lower() in response.answer.lower(), (
        f"Expected keyword '{expected_keyword}' in answer: '{response.answer}'"
    )


@pytest.mark.integration
@pytest.mark.parametrize("out_of_domain_query", [
    "What is the weather in Delhi right now?",
    "What are the guitar chords to play hotel california?",
    "Who won the football world cup in 2022?"
])
def test_out_of_domain_queries_escalate(rag_chain, out_of_domain_query):
    """Verify out-of-domain questions trigger human escalation."""
    response = rag_chain.answer(out_of_domain_query)

    assert response.escalate is True, (
        f"Out-of-domain query '{out_of_domain_query}' must trigger escalate=True. "
        f"Confidence was: {response.confidence}, Answer: {response.answer}"
    )


@pytest.mark.integration
def test_conversational_follow_up_rewriting(rag_chain):
    """Verify follow-up query rewriting preserves context across turns."""
    history = [
        {"role": "user", "content": "How long do I have to return a product?"},
        {"role": "assistant", "content": "ShopEase offers a 30-day standard return window from delivery date [1]."}
    ]
    follow_up = "What about damaged items?"
    response = rag_chain.answer(follow_up, history=history)

    assert response.answer, "Answer should not be empty"
    assert response.rewritten_query != follow_up, "Follow-up question should be rewritten"
    assert "damaged" in response.rewritten_query.lower()
    assert len(response.sources) > 0
