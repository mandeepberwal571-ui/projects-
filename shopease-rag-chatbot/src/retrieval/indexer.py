"""
Indexer runner for ShopEase document chunks.
Reads data/processed/chunks.json, embeds documents, and stores them in ChromaDB.

Usage:
python -m src.retrieval.indexer
python -m src.retrieval.indexer --reset
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from src.retrieval.config import (
    CHROMA_DIR,
    COLLECTION_NAME,
    PROCESSED_CHUNKS_PATH,
    validate_api_key,
)
from src.retrieval.vector_store import ShopEaseVectorStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("src.retrieval.indexer")


def main():
    parser = argparse.ArgumentParser(description="Index ShopEase document chunks into ChromaDB.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing collection and re-index from scratch."
    )
    args = parser.parse_args()

    print("\n" + "=" * 55)
    print("        ShopEase Vector Store Indexing Pipeline       ")
    print("=" * 55)

    # Validate API key
    try:
        validate_api_key()
    except ValueError as exc:
        logger.error("Configuration Error: %s", exc)
        print(f"\n[ERROR] {exc}\n")
        sys.exit(1)

    # Check chunks file
    if not PROCESSED_CHUNKS_PATH.exists():
        logger.error("Chunks file not found at: %s", PROCESSED_CHUNKS_PATH)
        print("\n[ERROR] Please run the ingestion pipeline first: python -m src.ingestion.run\n")
        sys.exit(1)

    with open(PROCESSED_CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"• Input chunks file:   {PROCESSED_CHUNKS_PATH.name} ({len(chunks)} chunks)")
    print(f"• ChromaDB location:   {CHROMA_DIR}")
    print(f"• Target collection:   {COLLECTION_NAME}")
    print(f"• Reset requested:     {args.reset}")
    print("-" * 55)

    store = ShopEaseVectorStore()

    if args.reset:
        logger.info("Resetting collection '%s'...", COLLECTION_NAME)
        store.delete_collection()

    initial_count = store.get_count()
    print(f"• Collection count before index: {initial_count}")

    logger.info("Indexing %d chunks...", len(chunks))
    indexed_count = store.add_documents(chunks)
    final_count = store.get_count()

    print("-" * 55)
    print("                  Indexing Complete!                 ")
    print("-" * 55)
    print(f"Chunks indexed this run:  {indexed_count}")
    print(f"Total collection count:   {final_count}")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()
