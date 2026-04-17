"""
DDAS – Hash Engine
Computes SHA-256 (and MD5) hashes for exact-duplicate detection.
"""

import hashlib
import os
from typing import Optional


CHUNK_SIZE = 65536  # 64 KB read chunks


def compute_sha256(filepath: str) -> Optional[str]:
    """Return hex-encoded SHA-256 digest of *filepath*, or None on error."""
    sha256 = hashlib.sha256()
    try:
        with open(filepath, "rb") as fh:
            for chunk in iter(lambda: fh.read(CHUNK_SIZE), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except (OSError, PermissionError):
        return None


def compute_md5(filepath: str) -> Optional[str]:
    """Return hex-encoded MD5 digest of *filepath*, or None on error."""
    md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as fh:
            for chunk in iter(lambda: fh.read(CHUNK_SIZE), b""):
                md5.update(chunk)
        return md5.hexdigest()
    except (OSError, PermissionError):
        return None


def hash_file(filepath: str) -> Optional[str]:
    """Primary entry-point: returns SHA-256 hash of *filepath*."""
    return compute_sha256(filepath)


def get_file_info(filepath: str) -> dict:
    """Return a dict with name, size, extension, and SHA-256 hash."""
    try:
        stat = os.stat(filepath)
        return {
            "file_name": os.path.basename(filepath),
            "file_path": filepath,
            "file_size": stat.st_size,
            "file_type": os.path.splitext(filepath)[1].lower().lstrip(".") or "unknown",
            "file_hash": compute_sha256(filepath),
        }
    except OSError:
        return {}
