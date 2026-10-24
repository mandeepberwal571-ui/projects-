"""
Main ingestion pipeline runner.
Processes all documents in data/raw/, cleans text, chunks content,
and writes structured chunk objects to data/processed/chunks.json.

Can be run via:
python -m src.ingestion.run
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from src.ingestion.cleaner import clean_text
from src.ingestion.chunker import RecursiveCharacterChunker
from src.ingestion.loaders import LOADER_MAPPING, load_document

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("src.ingestion.run")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_FILE = PROCESSED_DIR / "chunks.json"


def run_ingestion(
    raw_dir: Path = RAW_DIR,
    output_file: Path = OUTPUT_FILE,
    chunk_size: int = 800,
    chunk_overlap: int = 150
) -> List[Dict[str, Any]]:
    """
    Run full document ingestion pipeline:
    1. Scan raw_dir for supported files
    2. Load files page by page
    3. Clean and sanitize extracted text
    4. Chunk text recursively with metadata
    5. Save chunks to chunks.json
    """
    if not raw_dir.exists():
        logger.error("Raw data directory does not exist: %s", raw_dir)
        return []

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    chunker = RecursiveCharacterChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    all_chunks: List[Dict[str, Any]] = []
    files_processed = 0
    files_skipped = 0
    per_file_counts: Dict[str, int] = {}

    # Gather files
    supported_extensions = set(LOADER_MAPPING.keys())
    files = [
        f for f in sorted(raw_dir.iterdir())
        if f.is_file() and f.suffix.lower() in supported_extensions
    ]

    logger.info("Found %d supported document(s) in %s", len(files), raw_dir)

    for file_path in files:
        try:
            logger.info("Processing: %s", file_path.name)
            docs = load_document(file_path)
            if not docs:
                logger.warning("No extractable text found in %s", file_path.name)
                files_skipped += 1
                continue

            cleaned_docs: List[Dict[str, Any]] = []
            for doc in docs:
                cleaned = clean_text(doc.get("text", ""))
                if cleaned:
                    cleaned_docs.append({
                        "text": cleaned,
                        "metadata": doc.get("metadata", {})
                    })

            file_chunks = chunker.split_documents(cleaned_docs)
            all_chunks.extend(file_chunks)
            per_file_counts[file_path.name] = len(file_chunks)
            files_processed += 1
            logger.info("Generated %d chunk(s) for %s", len(file_chunks), file_path.name)

        except Exception as exc:
            logger.warning("Error processing file %s: %s (skipping)", file_path.name, exc, exc_info=False)
            files_skipped += 1

    # Save to disk
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    # Compute statistics
    total_chunks = len(all_chunks)
    total_chars = sum(len(c["text"]) for c in all_chunks)
    avg_len = round(total_chars / total_chunks, 1) if total_chunks > 0 else 0

    print("\n" + "=" * 50)
    print("       ShopEase Ingestion Pipeline Summary       ")
    print("=" * 50)
    print(f"Files processed:       {files_processed}")
    print(f"Files skipped:         {files_skipped}")
    print(f"Total chunks:          {total_chunks}")
    print(f"Average chunk length:  {avg_len} chars")
    print("-" * 50)
    print("Per-file breakdown:")
    for name, count in per_file_counts.items():
        print(f"  • {name:28} : {count:3} chunks")
    print("-" * 50)
    print(f"Output saved to: {output_file.relative_to(BASE_DIR)}")
    print("=" * 50 + "\n")

    return all_chunks


if __name__ == "__main__":
    run_ingestion()
