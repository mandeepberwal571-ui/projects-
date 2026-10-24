"""
ChromaDB Vector Store wrapper.
Handles collection persistence, document upsertion (deduplication via chunk_id),
cosine distance to similarity score conversion, and collection reset.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import chromadb
from chromadb.config import Settings

from src.retrieval.config import CHROMA_DIR, COLLECTION_NAME
from src.retrieval.embedder import GeminiEmbedder

logger = logging.getLogger(__name__)


class ShopEaseVectorStore:
    """
    Manages persistent ChromaDB vector storage and semantic retrieval for ShopEase.
    """

    def __init__(
        self,
        persist_directory: Path = CHROMA_DIR,
        collection_name: str = COLLECTION_NAME,
        embedder: Optional[GeminiEmbedder] = None
    ):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.embedder = embedder or GeminiEmbedder()

        # Initialize ChromaDB persistent client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )

        # Get or create collection with cosine distance metric
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def delete_collection(self) -> None:
        """Delete the current collection and reset state."""
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info("Deleted collection '%s'.", self.collection_name)
        except Exception as exc:
            logger.warning("Could not delete collection '%s': %s", self.collection_name, exc)

        # Recreate fresh collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def get_count(self) -> int:
        """Return total document count in the collection."""
        return self.collection.count()

    def add_documents(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Embed and upsert chunks into the ChromaDB collection.
        Uses deterministic chunk_id as the primary key to guarantee idempotency.
        """
        if not chunks:
            logger.warning("No chunks provided to add_documents.")
            return 0

        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for chunk in chunks:
            raw_meta = chunk.get("metadata", {})
            chunk_id = raw_meta.get("chunk_id")
            if not chunk_id:
                raise ValueError("Every chunk must contain a unique 'chunk_id' in metadata.")

            # Ensure metadata values are valid ChromaDB scalar types
            clean_meta = {}
            for k, v in raw_meta.items():
                if isinstance(v, (str, int, float, bool)):
                    clean_meta[k] = v
                elif v is None:
                    clean_meta[k] = ""
                else:
                    clean_meta[k] = str(v)

            ids.append(chunk_id)
            documents.append(chunk.get("text", ""))
            metadatas.append(clean_meta)

        logger.info("Generating embeddings for %d document chunks...", len(documents))
        embeddings = self.embedder.embed_documents(documents)

        logger.info("Upserting %d vectors into ChromaDB collection '%s'...", len(ids), self.collection_name)
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings
        )

        final_count = self.collection.count()
        logger.info("Upsert complete. Total collection count: %d", final_count)
        return len(ids)

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Semantic similarity search.
        Embeds the query using RETRIEVAL_QUERY and queries ChromaDB.
        Converts cosine distance to similarity score: (1.0 - distance).
        Returns a list of dictionaries: [{text, metadata, score}]
        """
        query_vec = self.embedder.embed_query(query)

        results = self.collection.query(
            query_embeddings=[query_vec],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        output: List[Dict[str, Any]] = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(docs, metas, distances):
            # In cosine space: similarity = 1.0 - distance
            similarity_score = max(0.0, round(1.0 - dist, 4))
            output.append({
                "text": doc,
                "metadata": meta,
                "score": similarity_score
            })

        return output
