"""
DDAS – Hash Engine
Computes SHA-256 hashes for exact duplicate detection.
"""

import hashlib
import os
from pathlib import Path


CHUNK_SIZE = 65536  # 64 KB


def compute_sha256(file_path: str) -> str:
    """Return the SHA-256 hex digest of *file_path*."""
    h = hashlib.sha256()
    with open(file_path, "rb") as fh:
        while chunk := fh.read(CHUNK_SIZE):
            h.update(chunk)
    return h.hexdigest()


def get_file_type(file_path: str) -> str:
    """Classify a file into a broad category based on its extension."""
    ext = Path(file_path).suffix.lower()
    categories = {
        "document": {".pdf", ".doc", ".docx", ".txt", ".odt", ".rtf", ".ppt", ".pptx", ".xls", ".xlsx"},
        "image":    {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".svg"},
        "video":    {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"},
        "audio":    {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"},
        "archive":  {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"},
        "code":     {".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".cs", ".go", ".rb"},
    }
    for category, extensions in categories.items():
        if ext in extensions:
            return category
    return "other"


def get_file_info(file_path: str) -> dict:
    """Return a dict with name, hash, type, size for *file_path*."""
    path = Path(file_path)
    return {
        "file_name": path.name,
        "file_hash": compute_sha256(file_path),
        "file_path": str(path.resolve()),
        "file_type": get_file_type(file_path),
        "file_size": path.stat().st_size,
    }
