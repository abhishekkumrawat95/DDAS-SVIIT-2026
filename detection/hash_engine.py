"""
DDAS – Hash Engine
Computes SHA-256 (and optional MD5) digests for files.
"""

import hashlib
import os
from pathlib import Path
from typing import Optional


CHUNK = 8 * 1024 * 1024   # 8 MB read buffer


def sha256(path: str | Path) -> Optional[str]:
    """
    Return the hex-encoded SHA-256 digest of *path*.
    Returns None if the file cannot be read.
    """
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(CHUNK), b""):
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError):
        return None


def md5(path: str | Path) -> Optional[str]:
    """
    Return the hex-encoded MD5 digest of *path*.
    Returns None if the file cannot be read.
    (MD5 is used only for quick preliminary checks, not as the primary key.)
    """
    try:
        h = hashlib.md5()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(CHUNK), b""):
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError):
        return None


def file_type(path: str | Path) -> str:
    """Return the lower-case file extension without the dot (e.g. 'pdf')."""
    return Path(path).suffix.lstrip(".").lower()


def file_size(path: str | Path) -> int:
    """Return the file size in bytes, or 0 on error."""
    try:
        return os.path.getsize(path)
    except OSError:
        return 0
