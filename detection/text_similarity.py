"""
DDAS – Text Similarity Engine
Uses TF-IDF + cosine similarity to find near-duplicate text documents.
Supports PDF, DOCX, and plain-text files.
"""

import os
import re
from typing import List, Optional, Tuple

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False


# ---------------------------------------------------------------------------
# Text extraction helpers
# ---------------------------------------------------------------------------

def _extract_pdf(filepath: str) -> str:
    """Extract text from a PDF file (requires pypdf or pdfminer)."""
    text = ""
    try:
        import pypdf
        with open(filepath, "rb") as fh:
            reader = pypdf.PdfReader(fh)
            for page in reader.pages:
                text += page.extract_text() or ""
    except ImportError:
        try:
            from pdfminer.high_level import extract_text as pdf_extract
            text = pdf_extract(filepath) or ""
        except ImportError:
            pass
    except Exception:
        pass
    return text


def _extract_docx(filepath: str) -> str:
    """Extract text from a DOCX file (requires python-docx)."""
    try:
        import docx
        doc = docx.Document(filepath)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        return ""


def extract_text_from_file(filepath: str) -> str:
    """
    Extract plain text from *filepath*.
    Supports .txt, .pdf, .docx, and falls back to raw read for other types.
    """
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == ".pdf":
            return _extract_pdf(filepath)
        if ext in (".docx", ".doc"):
            return _extract_docx(filepath)
        # Plain text / code files
        with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except (OSError, PermissionError):
        return ""


def _normalise(text: str) -> str:
    """Lower-case and collapse whitespace."""
    return re.sub(r"\s+", " ", text.lower()).strip()


# ---------------------------------------------------------------------------
# Similarity computation
# ---------------------------------------------------------------------------

def compute_text_similarity(text1: str, text2: str) -> float:
    """
    Return cosine similarity (0.0 – 1.0) between *text1* and *text2*.
    Returns 0.0 when scikit-learn is unavailable or texts are empty.
    """
    if not _SKLEARN_AVAILABLE:
        return 0.0
    t1, t2 = _normalise(text1), _normalise(text2)
    if not t1 or not t2:
        return 0.0
    vec = TfidfVectorizer().fit_transform([t1, t2])
    return float(cosine_similarity(vec[0], vec[1])[0][0])


def find_similar_documents(
    new_text: str,
    all_docs: List[Tuple[int, str]],
    threshold: float = 0.75,
) -> List[Tuple[int, float]]:
    """
    Compare *new_text* against *all_docs* (list of (id, text) tuples).
    Return a list of (doc_id, similarity_score) where score >= *threshold*.
    """
    if not _SKLEARN_AVAILABLE or not new_text or not all_docs:
        return []

    doc_ids = [doc_id for doc_id, _ in all_docs]
    texts = [_normalise(new_text)] + [_normalise(text) for _, text in all_docs]

    try:
        vec = TfidfVectorizer().fit_transform(texts)
        scores = cosine_similarity(vec[0:1], vec[1:]).flatten()
        return [
            (doc_ids[i], float(scores[i]))
            for i in range(len(doc_ids))
            if scores[i] >= threshold
        ]
    except Exception:
        return []


def is_text_file(filepath: str) -> bool:
    """Return True if *filepath* looks like a text/document file."""
    text_extensions = {
        ".txt", ".pdf", ".docx", ".doc", ".md", ".rst",
        ".csv", ".json", ".xml", ".html", ".py", ".java",
        ".c", ".cpp", ".js", ".ts", ".log",
    }
    return os.path.splitext(filepath)[1].lower() in text_extensions
