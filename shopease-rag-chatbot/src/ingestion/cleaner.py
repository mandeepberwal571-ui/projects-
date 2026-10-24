"""
Text cleaner module to normalize text before chunking and embedding.
"""

import re
import unicodedata


def clean_text(text: str) -> str:
    """
    Clean and normalize text:
    - Normalize Unicode characters (NFKC)
    - Remove zero-width spaces and non-printable characters
    - Normalize line breaks (CRLF -> LF)
    - Normalize multiple horizontal spaces and tabs into a single space
    - Collapse 3 or more consecutive newlines into 2 (standard paragraph break)
    - Strip leading and trailing whitespace
    """
    if not text:
        return ""

    # Normalize unicode
    text = unicodedata.normalize("NFKC", text)

    # Standardize line breaks
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove zero-width and unprintable control characters, but preserve \n and \t
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\u200B-\u200D\uFEFF]", "", text)

    # Normalize multiple horizontal spaces/tabs (preserving newlines)
    text = re.sub(r"[ \t]+", " ", text)

    # Clean spaces around newlines
    text = re.sub(r" *\n *", "\n", text)

    # Collapse 3 or more consecutive newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
