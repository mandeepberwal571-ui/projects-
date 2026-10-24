"""
Interactive retrieval demo & verification script for Phase 2.
Runs 5 realistic customer support queries against the ChromaDB vector store
and prints the top-3 retrieved chunks along with source citations and similarity scores.

Usage:
python tests/test_retrieval_demo.py
pytest tests/test_retrieval_demo.py -v
"""

import sys
from pathlib import Path

# Add project root to sys.path so script can be run directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.retrieval.vector_store import ShopEaseVectorStore

SAMPLE_QUERIES = [
    {
        "query": "How long do I have to return a product?",
        "expected_source": "return_policy.pdf"
    },
    {
        "query": "What does ERR_PAY_402 mean?",
        "expected_source": "troubleshooting_guide.docx"
    },
    {
        "query": "How do I reset my SmartBand X1?",
        "expected_source": "product_manual.pdf"
    },
    {
        "query": "Do you ship internationally?",
        "expected_source": "shipping_policy.txt"
    },
    {
        "query": "How do I contact support?",
        "expected_source": "warranty_and_support.md"
    }
]


def run_demo():
    print("\n" + "=" * 70)
    print("        ShopEase Semantic Retrieval Demo (Top-3 Results)        ")
    print("=" * 70)

    store = ShopEaseVectorStore()
    total_docs = store.get_count()
    print(f"Connected to ChromaDB. Total indexed chunks: {total_docs}\n")

    if total_docs == 0:
        print("[WARNING] ChromaDB collection is empty! Run indexer first:")
        print("  python -m src.retrieval.indexer --reset\n")
        return

    for idx, item in enumerate(SAMPLE_QUERIES, 1):
        q = item["query"]
        expected = item["expected_source"]

        print(f"\n[Query {idx}/5]: \"{q}\"")
        print(f"Expected Primary Source: {expected}")
        print("-" * 70)

        results = store.search(q, top_k=3)

        for rank, res in enumerate(results, 1):
            meta = res.get("metadata", {})
            source = meta.get("source", "unknown")
            page = meta.get("page", 1)
            chunk_id = meta.get("chunk_id", "n/a")
            score = res.get("score", 0.0)
            text_preview = res.get("text", "").replace("\n", " ")[:140]

            print(f"  #{rank} [Score: {score:.4f}] | {source} (Page {page}) [{chunk_id}]")
            print(f"     Snippet: \"{text_preview}...\"\n")

    print("=" * 70)
    print("Retrieval demo completed successfully.")
    print("=" * 70 + "\n")


def test_retrieval_queries():
    """Automated test validating that ChromaDB returns valid results for all 5 queries."""
    store = ShopEaseVectorStore()
    if store.get_count() == 0:
        return  # Skip if indexer has not yet been executed in CI

    for item in SAMPLE_QUERIES:
        q = item["query"]
        results = store.search(q, top_k=3)
        assert len(results) > 0
        assert results[0]["score"] > 0.4
        assert "source" in results[0]["metadata"]
        assert "chunk_id" in results[0]["metadata"]


if __name__ == "__main__":
    run_demo()
