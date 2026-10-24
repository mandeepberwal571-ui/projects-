"""
Custom Recursive Character Text Splitter written from scratch (zero LangChain dependencies).
Splits documents using a hierarchy of separators, respects chunk_size and overlap,
and produces deterministic metadata and chunk IDs.
"""

from typing import Any, Dict, List, Optional


class RecursiveCharacterChunker:
    """
    Splits text recursively using an ordered list of separators.
    Default separators: ["\\n\\n", "\\n", ". ", " "]
    """

    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
        separators: Optional[List[str]] = None
    ):
        if chunk_overlap >= chunk_size:
            raise ValueError(f"chunk_overlap ({chunk_overlap}) must be smaller than chunk_size ({chunk_size})")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " "]

    def _get_overlap(self, text: str) -> str:
        """Extract a clean tail portion of text up to chunk_overlap length."""
        if not text or self.chunk_overlap <= 0:
            return ""
        slice_text = text[-self.chunk_overlap:]
        # Find first word boundary to avoid partial words
        space_idx = slice_text.find(" ")
        if space_idx != -1 and space_idx < len(slice_text) - 1:
            return slice_text[space_idx + 1:].strip()
        return slice_text.strip()

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """Recursively split text by the first matching separator."""
        text = text.strip()
        if not text:
            return []

        if len(text) <= self.chunk_size:
            return [text]

        # Find the best separator available
        chosen_separator = ""
        for sep in separators:
            if sep in text:
                chosen_separator = sep
                break

        # If no separator found, hard slice text
        if not chosen_separator:
            chunks = []
            start = 0
            while start < len(text):
                end = min(start + self.chunk_size, len(text))
                slice_chunk = text[start:end].strip()
                if slice_chunk:
                    chunks.append(slice_chunk)
                if end >= len(text):
                    break
                start = end - self.chunk_overlap
            return chunks

        # Split using the chosen separator
        splits = text.split(chosen_separator)
        
        # Merge splits up to chunk_size
        good_chunks: List[str] = []
        current_doc: List[str] = []
        total_len = 0

        for split in splits:
            split_len = len(split)
            # If an individual split is too big, recursively break it down
            if split_len > self.chunk_size:
                if current_doc:
                    merged = chosen_separator.join(current_doc).strip()
                    if merged:
                        good_chunks.append(merged)
                    current_doc = []
                    total_len = 0

                # Split further using subsequent separators
                remaining_seps = [s for s in self.separators if s != chosen_separator]
                sub_chunks = self._split_text(split, remaining_seps)
                good_chunks.extend(sub_chunks)
                continue

            sep_len = len(chosen_separator) if current_doc else 0
            if total_len + sep_len + split_len <= self.chunk_size:
                current_doc.append(split)
                total_len += sep_len + split_len
            else:
                if current_doc:
                    merged = chosen_separator.join(current_doc).strip()
                    if merged:
                        good_chunks.append(merged)
                        overlap_prefix = self._get_overlap(merged)
                        if overlap_prefix:
                            current_doc = [overlap_prefix, split]
                            total_len = len(overlap_prefix) + len(chosen_separator) + len(split)
                        else:
                            current_doc = [split]
                            total_len = len(split)
                else:
                    current_doc = [split]
                    total_len = len(split)

        if current_doc:
            merged = chosen_separator.join(current_doc).strip()
            if merged and (not good_chunks or merged != good_chunks[-1]):
                good_chunks.append(merged)

        return good_chunks

    def split_text(self, text: str) -> List[str]:
        """Split raw text into chunks."""
        return self._split_text(text, self.separators)

    def split_document(self, doc: Dict[str, Any], start_chunk_idx: int = 1) -> List[Dict[str, Any]]:
        """
        Split a loaded document dictionary into chunk dictionaries.
        doc: {"text": str, "metadata": {"source": str, "page": int, ...}}
        Returns: list of {"text": str, "metadata": {...}}
        """
        raw_text = doc.get("text", "")
        base_meta = doc.get("metadata", {})
        source = base_meta.get("source", "unknown")
        page = base_meta.get("page", 1)

        text_chunks = self.split_text(raw_text)
        result: List[Dict[str, Any]] = []

        for idx, chunk_text in enumerate(text_chunks):
            chunk_num = start_chunk_idx + idx
            chunk_id = f"{source}::p{page}::c{chunk_num}"
            chunk_meta = {
                **base_meta,
                "chunk_id": chunk_id,
                "chunk_index": chunk_num,
                "char_length": len(chunk_text),
            }
            result.append({
                "text": chunk_text,
                "metadata": chunk_meta
            })

        return result

    def split_documents(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Split a list of documents. Tracks per-file-and-page chunk index.
        """
        all_chunks: List[Dict[str, Any]] = []
        # Track counter per (source, page)
        counters: Dict[tuple, int] = {}

        for doc in docs:
            source = doc.get("metadata", {}).get("source", "unknown")
            page = doc.get("metadata", {}).get("page", 1)
            key = (source, page)
            start_idx = counters.get(key, 1)

            chunks = self.split_document(doc, start_chunk_idx=start_idx)
            counters[key] = start_idx + len(chunks)
            all_chunks.extend(chunks)

        return all_chunks
