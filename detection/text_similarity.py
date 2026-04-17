"""
DDAS – Text Similarity Engine
TF-IDF cosine similarity for document duplicates.
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    _HAS_SKLEARN = True
except ImportError:
    _HAS_SKLEARN = False

# Cap plain-text extraction at ~200 KB to avoid memory issues on large files
MAX_TEXT_BYTES = 200_000


def _clean(text: str) -> str:
    """Lowercase and strip punctuation."""
    return re.sub(r"[^\w\s]", " ", text.lower())


def extract_text_from_file(path: str) -> Optional[str]:
    """
    Try to read plain text from *path*.
    Falls back gracefully for binary files.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            raw = fh.read(MAX_TEXT_BYTES)
        return _clean(raw) if raw.strip() else None
    except (OSError, PermissionError):
        return None


def find_similar(
    new_text: str,
    corpus: List[Tuple[int, str]],   # [(id, text), ...]
    threshold: float = 0.75,
) -> Optional[Tuple[int, float]]:
    """
    Compare *new_text* against *corpus* using TF-IDF cosine similarity.

    Returns (corpus_id, similarity_score) of the best match if it meets
    *threshold*, otherwise None.
    """
    if not _HAS_SKLEARN:
        return None
    if not corpus:
        return None

    texts = [new_text] + [t for _, t in corpus]
    try:
        vec = TfidfVectorizer(min_df=1, stop_words="english")
        tfidf = vec.fit_transform(texts)
    except ValueError:
        return None

    sims = cosine_similarity(tfidf[0:1], tfidf[1:]).flatten()
    best_idx = int(sims.argmax())
    best_score = float(sims[best_idx])

    if best_score >= threshold:
        return corpus[best_idx][0], best_score
    return None
