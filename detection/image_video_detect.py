"""
DDAS – Image & Video Duplicate Detection
Uses perceptual hashing (pHash) for images and frame-sampling for video.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

try:
    from PIL import Image
    import imagehash
    _HAS_IMAGEHASH = True
except ImportError:
    _HAS_IMAGEHASH = False

try:
    import cv2
    import numpy as np
    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
VIDEO_EXTS = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"}


# ── Images ────────────────────────────────────────────────────────────────────

def image_phash(path: str | Path) -> Optional[str]:
    """Return a hex pHash string for *path*, or None on failure."""
    if not _HAS_IMAGEHASH:
        return None
    try:
        img = Image.open(path).convert("RGB")
        return str(imagehash.phash(img))
    except Exception:
        return None


def images_are_similar(hash1: str, hash2: str, threshold: int = 10) -> bool:
    """
    Return True when the Hamming distance between two hex pHash strings
    is at most *threshold*.
    """
    if not _HAS_IMAGEHASH:
        return False
    try:
        h1 = imagehash.hex_to_hash(hash1)
        h2 = imagehash.hex_to_hash(hash2)
        return (h1 - h2) <= threshold
    except Exception:
        return False


# ── Video ─────────────────────────────────────────────────────────────────────

def video_fingerprint(path: str | Path, n_frames: int = 10) -> Optional[str]:
    """
    Sample *n_frames* evenly through the video, compute a pHash for each,
    and return them concatenated as a single fingerprint string.
    Returns None when OpenCV or imagehash is unavailable, or on error.
    """
    if not (_HAS_CV2 and _HAS_IMAGEHASH):
        return None
    try:
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            return None
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total < 1:
            cap.release()
            return None

        hashes: list[str] = []
        step = max(1, total // n_frames)
        for i in range(n_frames):
            cap.set(cv2.CAP_PROP_POS_FRAMES, min(i * step, total - 1))
            ok, frame = cap.read()
            if not ok:
                continue
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            hashes.append(str(imagehash.phash(img)))
        cap.release()
        return "|".join(hashes) if hashes else None
    except Exception:
        return None


def videos_are_similar(fp1: str, fp2: str, threshold: int = 10) -> bool:
    """
    Return True when the average Hamming distance between frame hashes
    of two video fingerprints is at most *threshold*.
    """
    if not _HAS_IMAGEHASH:
        return False
    try:
        h1 = fp1.split("|")
        h2 = fp2.split("|")
        pairs = list(zip(h1, h2))
        if not pairs:
            return False
        total = sum(
            imagehash.hex_to_hash(a) - imagehash.hex_to_hash(b)
            for a, b in pairs
        )
        return (total / len(pairs)) <= threshold
    except Exception:
        return False


# ── Extension helpers ─────────────────────────────────────────────────────────

def is_image(path: str | Path) -> bool:
    return Path(path).suffix.lower() in IMAGE_EXTS


def is_video(path: str | Path) -> bool:
    return Path(path).suffix.lower() in VIDEO_EXTS
