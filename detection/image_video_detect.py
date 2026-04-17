"""
DDAS – Image & Video Detection
Perceptual hash (pHash) for images; frame-sampling fingerprint for videos.
"""

import os
from typing import Optional

try:
    import imagehash
    from PIL import Image
    _IMG_AVAILABLE = True
except ImportError:
    _IMG_AVAILABLE = False

try:
    import cv2
    import numpy as np
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}


# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------

def compute_image_phash(filepath: str) -> Optional[str]:
    """Return perceptual hash string for an image, or None on error."""
    if not _IMG_AVAILABLE:
        return None
    try:
        img = Image.open(filepath)
        return str(imagehash.phash(img))
    except Exception:
        return None


def images_are_similar(hash1: str, hash2: str, threshold: int = 10) -> bool:
    """Return True when two pHash strings differ by <= *threshold* bits."""
    if not _IMG_AVAILABLE or not hash1 or not hash2:
        return False
    try:
        h1 = imagehash.hex_to_hash(hash1)
        h2 = imagehash.hex_to_hash(hash2)
        return (h1 - h2) <= threshold
    except Exception:
        return False


def image_hash_distance(hash1: str, hash2: str) -> int:
    """Hamming distance between two pHash strings (lower = more similar)."""
    if not _IMG_AVAILABLE or not hash1 or not hash2:
        return 999
    try:
        h1 = imagehash.hex_to_hash(hash1)
        h2 = imagehash.hex_to_hash(hash2)
        return int(h1 - h2)
    except Exception:
        return 999


# ---------------------------------------------------------------------------
# Video helpers
# ---------------------------------------------------------------------------

def compute_video_fingerprint(filepath: str, num_frames: int = 10) -> Optional[str]:
    """
    Sample *num_frames* evenly-spaced frames from a video and return
    a concatenated perceptual-hash string as fingerprint.
    Returns None when OpenCV or Pillow is unavailable.
    """
    if not _CV2_AVAILABLE or not _IMG_AVAILABLE:
        return None
    try:
        cap = cv2.VideoCapture(filepath)
        if not cap.isOpened():
            return None
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total <= 0:
            cap.release()
            return None
        step = max(1, total // num_frames)
        hashes = []
        for idx in range(0, total, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret:
                continue
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            hashes.append(str(imagehash.phash(img)))
            if len(hashes) >= num_frames:
                break
        cap.release()
        return "|".join(hashes) if hashes else None
    except Exception:
        return None


def videos_are_similar(fp1: str, fp2: str, threshold: int = 10) -> bool:
    """
    Return True if two video fingerprints are considered similar.
    Compares each sampled-frame hash pair and checks the average distance.
    """
    if not fp1 or not fp2:
        return False
    hashes1 = fp1.split("|")
    hashes2 = fp2.split("|")
    pairs = min(len(hashes1), len(hashes2))
    if pairs == 0:
        return False
    total_dist = sum(
        image_hash_distance(hashes1[i], hashes2[i]) for i in range(pairs)
    )
    return (total_dist / pairs) <= threshold


def is_image_file(filepath: str) -> bool:
    return os.path.splitext(filepath)[1].lower() in IMAGE_EXTENSIONS


def is_video_file(filepath: str) -> bool:
    return os.path.splitext(filepath)[1].lower() in VIDEO_EXTENSIONS
