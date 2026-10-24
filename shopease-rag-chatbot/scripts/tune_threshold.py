"""
Threshold Tuning Script for ShopEase RAG Pipeline.
Evaluates 8 in-domain e-commerce questions against 8 out-of-domain general questions
to calibrate the optimal SIMILARITY_THRESHOLD for human escalation.

Usage:
python scripts/tune_threshold.py
python scripts/tune_threshold.py --apply
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.retrieval.vector_store import ShopEaseVectorStore

IN_DOMAIN_QUESTIONS = [
    "How many days do I have to return an item?",
    "What should I do if my package arrived damaged?",
    "How do I fix error code ERR_PAY_402?",
    "What are the steps to factory reset my SmartBand X1?",
    "What are the shipping charges for domestic standard delivery?",
    "Does the ShopEase limited warranty cover battery degradation?",
    "How do I reset my account password if I am locked out?",
    "How do I contact customer support by phone?"
]

OUT_OF_DOMAIN_QUESTIONS = [
    "What is the current weather forecast in New Delhi?",
    "Who won the ICC Cricket World Cup in 2023?",
    "How do I bake a moist double-chocolate fudge cake?",
    "Can you book me a direct flight from New York to London?",
    "What is the current stock price of Tesla today?",
    "Who is the current President of France?",
    "What are the acoustic guitar chords for Let It Be?",
    "Write a Python script to calculate the Fibonacci sequence."
]


def evaluate_queries(store: ShopEaseVectorStore, queries: list[str]) -> list[dict]:
    results = []
    for q in queries:
        matches = store.search(q, top_k=1)
        top_score = matches[0]["score"] if matches else 0.0
        top_source = matches[0]["metadata"].get("source", "n/a") if matches else "n/a"
        results.append({
            "query": q,
            "score": top_score,
            "source": top_source
        })
    return results


def main():
    parser = argparse.ArgumentParser(description="Tune SIMILARITY_THRESHOLD for RAG pipeline.")
    parser.add_argument("--apply", action="store_true", help="Automatically update SIMILARITY_THRESHOLD in src/llm/config.py")
    args = parser.parse_args()

    print("\n" + "=" * 76)
    print("       ShopEase RAG Similarity Threshold Calibration Benchmark       ")
    print("=" * 76)

    store = ShopEaseVectorStore()
    if store.get_count() == 0:
        print("[ERROR] Vector store is empty. Please run: python -m src.retrieval.indexer")
        sys.exit(1)

    print("\nEvaluating 8 IN-DOMAIN queries...")
    in_results = evaluate_queries(store, IN_DOMAIN_QUESTIONS)
    in_scores = [r["score"] for r in in_results]

    print("\nEvaluating 8 OUT-OF-DOMAIN queries...")
    out_results = evaluate_queries(store, OUT_OF_DOMAIN_QUESTIONS)
    out_scores = [r["score"] for r in out_results]

    print("\n" + "-" * 76)
    print(f"{'QUERY':<52} | {'SCORE':<7} | {'TOP SOURCE'}")
    print("-" * 76)
    print("--- [IN-DOMAIN QUERIES] ---")
    for r in in_results:
        print(f"{r['query'][:50]:<52} | {r['score']:<7.4f} | {r['source']}")

    print("\n--- [OUT-OF-DOMAIN QUERIES] ---")
    for r in out_results:
        print(f"{r['query'][:50]:<52} | {r['score']:<7.4f} | {r['source']}")

    # Statistics
    min_in = min(in_scores)
    max_in = max(in_scores)
    avg_in = sum(in_scores) / len(in_scores)

    min_out = min(out_scores)
    max_out = max(out_scores)
    avg_out = sum(out_scores) / len(out_scores)

    print("\n" + "=" * 76)
    print("                      Benchmark Statistics                     ")
    print("=" * 76)
    print(f"In-Domain Scores:     Min = {min_in:.4f} | Max = {max_in:.4f} | Mean = {avg_in:.4f}")
    print(f"Out-of-Domain Scores: Min = {min_out:.4f} | Max = {max_out:.4f} | Mean = {avg_out:.4f}")
    print("-" * 76)

    # Calculate optimal threshold
    if min_in > max_out:
        suggested_threshold = round((min_in + max_out) / 2.0, 2)
        print(f"Perfect separation detected! Suggested Threshold = {suggested_threshold:.2f}")
    else:
        # If slight overlap occurs, place threshold just below the in-domain average or above out-of-domain average
        suggested_threshold = round((avg_in + avg_out) / 2.0, 2)
        print(f"Partial distribution overlap observed. Balanced Suggested Threshold = {suggested_threshold:.2f}")

    print(f"\nRecommended config.py update: SIMILARITY_THRESHOLD = {suggested_threshold:.2f}")
    print("=" * 76 + "\n")

    if args.apply:
        config_path = PROJECT_ROOT / "src" / "llm" / "config.py"
        content = config_path.read_text(encoding="utf-8")
        import re
        new_content = re.sub(
            r"SIMILARITY_THRESHOLD = \d+\.\d+",
            f"SIMILARITY_THRESHOLD = {suggested_threshold:.2f}",
            content
        )
        config_path.write_text(new_content, encoding="utf-8")
        print(f"Successfully applied SIMILARITY_THRESHOLD = {suggested_threshold:.2f} to {config_path.name}!\n")


if __name__ == "__main__":
    main()
