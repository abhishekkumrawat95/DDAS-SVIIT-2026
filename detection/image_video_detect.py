"""
DDAS – Image & Video Detection Engine
Uses perceptual hashing (pHash) for images and frame-sampling for videos.
"""

import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

try:
    from PIL import Image
    import imagehash
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

try:
    import cv2
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"}


# ── Images ────────────────────────────────────────────────────────────────────

def compute_image_phash(file_path: str) -> Optional[str]:
    """Return the perceptual hash string of an image, or None on error."""
    if not _PIL_AVAILABLE:
        return None
    try:
        img = Image.open(file_path).convert("RGB")
        return str(imagehash.phash(img))
    except Exception:
        return None


def images_are_duplicate(hash_a: str, hash_b: str) -> Tuple[bool, int]:
    """
    Compare two pHash strings.
    Returns (is_duplicate, hamming_distance).
    """
    try:
        dist = imagehash.hex_to_hash(hash_a) - imagehash.hex_to_hash(hash_b)
        return dist <= config.IMAGE_HASH_THRESHOLD, dist
    except Exception:
        return False, 999


# ── Videos ───────────────────────────────────────────────────────────────────

def compute_video_fingerprint(file_path: str, sample_count: int = 5) -> Optional[str]:
    """
    Sample *sample_count* evenly-spaced frames from a video and return a
    concatenated pHash fingerprint string, or None on error.
    """
    if not _CV2_AVAILABLE or not _PIL_AVAILABLE:
        return None
    cap = cv2.VideoCapture(file_path)
    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            return None
        step = max(1, total_frames // sample_count)
        hashes = []
        for i in range(sample_count):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i * step)
            ret, frame = cap.read()
            if not ret:
                break
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            hashes.append(str(imagehash.phash(img)))
        return "|".join(hashes) if hashes else None
    except Exception:
        return None
    finally:
        cap.release()


def videos_are_duplicate(fp_a: str, fp_b: str) -> Tuple[bool, float]:
    """
    Compare two video fingerprints (pipe-separated pHash strings).
    Returns (is_duplicate, average_similarity_fraction).
    """
    try:
        hashes_a = fp_a.split("|")
        hashes_b = fp_b.split("|")
        pairs = zip(hashes_a, hashes_b)
        distances = [
            imagehash.hex_to_hash(a) - imagehash.hex_to_hash(b)
            for a, b in pairs
        ]
        avg = sum(distances) / len(distances) if distances else 999
        return avg <= config.IMAGE_HASH_THRESHOLD, 1 - avg / 64
    except Exception:
        return False, 0.0


# ── Typing fix ────────────────────────────────────────────────────────────────
from typing import Tuple  # noqa: E402  (moved here to avoid shadowing above)
