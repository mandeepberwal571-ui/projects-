"""
Document loaders for PDF, DOCX, TXT, and Markdown files.
Each loader returns a list of dictionaries with structure:
[
    {
        "text": str,
        "metadata": {
            "source": str,
            "page": int
        }
    },
    ...
]
"""

import logging
from pathlib import Path
from typing import Any, Dict, List
import pypdf
import docx

logger = logging.getLogger(__name__)


def load_pdf(file_path: str | Path) -> List[Dict[str, Any]]:
    """Load a PDF document page by page."""
    path = Path(file_path)
    documents: List[Dict[str, Any]] = []
    
    reader = pypdf.PdfReader(str(path))
    total_pages = len(reader.pages)
    
    for page_idx, page in enumerate(reader.pages):
        page_num = page_idx + 1
        page_text = page.extract_text() or ""
        if page_text.strip():
            documents.append({
                "text": page_text,
                "metadata": {
                    "source": path.name,
                    "page": page_num,
                    "total_pages": total_pages
                }
            })
            
    return documents


def load_docx(file_path: str | Path) -> List[Dict[str, Any]]:
    """Load a DOCX document extracting paragraphs and tables."""
    path = Path(file_path)
    doc = docx.Document(str(path))
    
    content_parts: List[str] = []
    
    for para in doc.paragraphs:
        if para.text.strip():
            content_parts.append(para.text)
            
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                content_parts.append(row_text)
                
    full_text = "\n\n".join(content_parts)
    if not full_text.strip():
        return []
        
    return [{
        "text": full_text,
        "metadata": {
            "source": path.name,
            "page": 1
        }
    }]


def load_txt(file_path: str | Path) -> List[Dict[str, Any]]:
    """Load a plain text file."""
    path = Path(file_path)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="latin-1")
        
    if not text.strip():
        return []
        
    return [{
        "text": text,
        "metadata": {
            "source": path.name,
            "page": 1
        }
    }]


def load_markdown(file_path: str | Path) -> List[Dict[str, Any]]:
    """Load a markdown file."""
    path = Path(file_path)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="latin-1")
        
    if not text.strip():
        return []
        
    return [{
        "text": text,
        "metadata": {
            "source": path.name,
            "page": 1
        }
    }]


LOADER_MAPPING = {
    ".pdf": load_pdf,
    ".docx": load_docx,
    ".txt": load_txt,
    ".md": load_markdown,
}


def load_document(file_path: str | Path) -> List[Dict[str, Any]]:
    """
    Dispatch document loading based on file extension.
    Skips unsupported files with a warning.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()
    
    loader_func = LOADER_MAPPING.get(suffix)
    if not loader_func:
        raise ValueError(f"Unsupported file type: {suffix} for file {path.name}")
        
    return loader_func(path)
