"""
DDAS – Text Similarity Engine
Uses TF-IDF cosine similarity to detect near-duplicate documents.
"""

import sys
from pathlib import Path
from typing import List, Tuple, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False


def extract_text(file_path: str) -> Optional[str]:
    """Extract plain text from a file (best-effort for .txt files)."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except Exception:
        return None


def compute_similarity(text_a: str, text_b: str) -> float:
    """Return cosine similarity [0.0 – 1.0] between two text strings."""
    if not _SKLEARN_AVAILABLE:
        return 0.0
    if not text_a or not text_b:
        return 0.0
    vectorizer = TfidfVectorizer()
    try:
        tfidf = vectorizer.fit_transform([text_a, text_b])
        score = cosine_similarity(tfidf[0], tfidf[1])[0][0]
        return float(score)
    except ValueError:
        return 0.0


def find_similar_in_corpus(
    query_text: str,
    corpus: List[Tuple[int, str]],
    threshold: float = config.TEXT_SIMILARITY_THRESHOLD,
) -> List[Tuple[int, float]]:
    """
    Return a list of (doc_id, similarity) tuples from *corpus* whose
    similarity to *query_text* is >= *threshold*.

    corpus: list of (id, text) tuples as returned by get_all_docs_for_similarity()
    """
    if not _SKLEARN_AVAILABLE or not query_text or not corpus:
        return []

    ids = [row[0] for row in corpus]
    texts = [row[1] for row in corpus]
    all_texts = [query_text] + texts

    vectorizer = TfidfVectorizer()
    try:
        tfidf = vectorizer.fit_transform(all_texts)
    except ValueError:
        return []

    scores = cosine_similarity(tfidf[0:1], tfidf[1:])[0]
    results = [
        (ids[i], float(scores[i]))
        for i in range(len(ids))
        if scores[i] >= threshold
    ]
    results.sort(key=lambda x: x[1], reverse=True)
    return results
