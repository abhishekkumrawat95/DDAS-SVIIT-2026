"""
DDAS – Chatbot Engine
Answers natural-language queries about files stored in the DDAS database.

Enhanced with AI-like semantic understanding:
  • Date filtering  – "today", "yesterday", "this week", "this month",
                       "last month", explicit date ranges
  • File-type filter – "pdf", "txt", "docx", "mp4", etc.
  • User filter      – "files from john", "show john's files"
  • Size filter      – "files larger than 1mb", "size > 500kb"
  • Cross-user dups  – "duplicates between john and jane"
  • Keyword search   – any unmatched words become a DB keyword search
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db.db_helper import (
    search_files_by_keyword,
    get_all_downloads,
    get_all_alerts,
    get_stats,
    search_files_by_type,
    search_files_by_user,
    search_files_by_date_range,
    search_files_by_size,
    get_cross_user_duplicates,
)


# ── Intent patterns (ordered most-specific first) ─────────────────────────────

_INTENTS: List[Tuple[str, str]] = [
    (r"\b(hi|hello|hey)\b",                               "greet"),
    (r"\b(bye|exit|quit|goodbye)\b",                      "goodbye"),
    (r"\bhelp\b",                                         "help"),
    (r"\bstats?\b|\b(statistic|summary|count)\b",         "stats"),
    # Cross-user duplicate query: "duplicates between X and Y"
    (r"\bduplicate[s]?\s+between\b",                      "cross_user_dups"),
    (r"\bduplicates?\b.*\buser[s]?\b",                    "cross_user_dups"),
    # Alerts / duplicates listing
    (r"\balerts?\b|\bduplicates?\b|\bwarn\b",             "alerts"),
    # Date-range queries (before type/user so compound queries resolve to date)
    (r"\btoday\b",                                         "by_date_today"),
    (r"\byesterday\b",                                     "by_date_yesterday"),
    (r"\bthis\s+week\b",                                   "by_date_week"),
    (r"\bthis\s+month\b",                                  "by_date_month"),
    (r"\blast\s+month\b",                                  "by_date_last_month"),
    # Size queries: "> 1mb", "larger than 500kb", "size > 1mb"
    (r"\b(larger|bigger|greater|more|>|above)\b.*\b(\d+)\s*(kb|mb|gb|b)\b", "by_size_gt"),
    (r"\b(\d+)\s*(kb|mb|gb|b)\b.*\b(larger|bigger|greater|more|>|above)\b", "by_size_gt"),
    (r"\bsize\s*[>]\s*(\d+)\s*(kb|mb|gb|b)?\b",                              "by_size_gt"),
    # File-type queries: "show all pdfs", "find txt files", "show me all txt files"
    # (before list_all so type-specific queries win over generic ones)
    (
        r"\b(pdf|pdfs|txt|docx?|xlsx?|csv|mp[34]|avi|mkv|mov|jpg|jpeg|png|gif|zip|rar|exe|py|js|html?|md)s?\b",
        "by_type",
    ),
    # User queries: "files from john", "john's files", "user john"
    (r"\bfrom\s+(?:user\s+)?(\w+)\b|\buser\s+(\w+)\b|\b(\w+)[''s]+\s+files?\b", "by_user"),
    # Generic list-all
    (r"\b(all|every)\b.*\bfiles?\b",                       "list_all"),
    (r"\b(show|list)\b.*\b(files?|downloads?)\b",          "list_all"),
    (r"\b(search|find|look|where|who)\b",                  "search"),
]

_HELP_TEXT = """
I can answer questions like:
  • "search invoice"                  – find files containing 'invoice'
  • "show all files"                  – list every downloaded file
  • "show all PDFs"                   – list files by type
  • "find txt files"                  – list .txt downloads
  • "files from user john"            – list files downloaded by john
  • "files downloaded today"          – date-filtered list
  • "files this month"                – list this month's downloads
  • "files larger than 1MB"           – size-filtered list
  • "duplicates between john and jane"– cross-user duplicate pairs
  • "show alerts"                     – duplicate alert history
  • "stats"                           – system summary
  • "help"                            – this message
  • "bye"                             – exit the chatbot
""".strip()


# ── Date helpers ──────────────────────────────────────────────────────────────

def _today_range() -> Tuple[str, str]:
    today = date.today()
    return today.isoformat(), (today + timedelta(days=1)).isoformat()


def _yesterday_range() -> Tuple[str, str]:
    yesterday = date.today() - timedelta(days=1)
    return yesterday.isoformat(), date.today().isoformat()


def _this_week_range() -> Tuple[str, str]:
    today = date.today()
    start = today - timedelta(days=today.weekday())   # Monday
    return start.isoformat(), (today + timedelta(days=1)).isoformat()


def _this_month_range() -> Tuple[str, str]:
    today = date.today()
    start = today.replace(day=1)
    return start.isoformat(), (today + timedelta(days=1)).isoformat()


def _last_month_range() -> Tuple[str, str]:
    today = date.today()
    first_of_this = today.replace(day=1)
    last_month_end = first_of_this - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    return last_month_start.isoformat(), first_of_this.isoformat()


# ── Size helpers ──────────────────────────────────────────────────────────────

_SIZE_UNITS = {"b": 1, "kb": 1024, "mb": 1024 ** 2, "gb": 1024 ** 3}


def _parse_size_bytes(text: str) -> Optional[int]:
    """Extract a byte count from strings like '1MB', '500kb', '2 GB'."""
    m = re.search(r"(\d+(?:\.\d+)?)\s*(kb|mb|gb|b)\b", text.lower())
    if not m:
        return None
    value, unit = float(m.group(1)), m.group(2)
    return int(value * _SIZE_UNITS.get(unit, 1))


# ── Extraction helpers ────────────────────────────────────────────────────────

_FILE_TYPES = {
    "pdf", "txt", "doc", "docx", "xls", "xlsx", "csv",
    "mp3", "mp4", "avi", "mkv", "mov", "wav", "flac",
    "jpg", "jpeg", "png", "gif", "bmp", "svg", "webp",
    "zip", "rar", "7z", "tar", "gz",
    "exe", "msi", "py", "js", "html", "htm", "md", "json", "xml",
}


def _extract_file_type(text: str) -> Optional[str]:
    """Return the first recognised file-type word found in *text*.
    Handles plural forms (e.g. 'pdfs' → 'pdf').
    """
    for word in re.split(r"\W+", text.lower()):
        w = word.lstrip(".")
        if w in _FILE_TYPES:
            return w
        # Try stripping a trailing 's' for plural forms (e.g. 'pdfs' → 'pdf')
        if w.endswith("s") and w[:-1] in _FILE_TYPES:
            return w[:-1]
    return None


def _extract_username(text: str) -> Optional[str]:
    """
    Try to pull a username from phrases like:
      "files from john", "show john's files", "user john", "show user john"
    """
    patterns = [
        r"\bfrom\s+(?:user\s+)?([A-Za-z0-9_]+)",
        r"\buser\s+([A-Za-z0-9_]+)",
        r"\b([A-Za-z0-9_]+)[''s]+\s+files?\b",
        r"\bshow\s+([A-Za-z0-9_]+)(?:\s+files?)?\b",
    ]
    stop_words = {
        "all", "the", "a", "an", "me", "my", "our", "your",
        "show", "list", "find", "search", "file", "files", "download",
        "downloads", "duplicate", "duplicates", "alert", "alerts",
        "today", "yesterday", "week", "month", "last", "this",
    }
    for pat in patterns:
        m = re.search(pat, text.lower())
        if m:
            name = m.group(1)
            if name not in stop_words:
                return name
    return None


def _extract_two_users(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract two usernames from 'duplicates between X and Y' style queries.
    """
    m = re.search(
        r"\bbetween\s+([A-Za-z0-9_]+)\s+and\s+([A-Za-z0-9_]+)\b",
        text.lower(),
    )
    if m:
        return m.group(1), m.group(2)
    # Fallback: try 'X and Y duplicates'
    m = re.search(
        r"\b([A-Za-z0-9_]+)\s+and\s+([A-Za-z0-9_]+)\s+duplicates?\b",
        text.lower(),
    )
    if m:
        return m.group(1), m.group(2)
    return None, None


def _extract_keyword(text: str) -> str:
    """Strip common stop-words and return the most likely search keyword."""
    stop = {
        "search", "find", "look", "for", "where", "is", "the", "a", "an",
        "show", "me", "please", "file", "files", "download", "downloads", "any",
        "all", "every", "list", "get",
    }
    tokens = [w for w in re.split(r"\W+", text.lower()) if w and w not in stop]
    return " ".join(tokens[:5]) if tokens else text.strip()


# ── Formatting helpers ────────────────────────────────────────────────────────

def _fmt_files(rows: list) -> str:
    if not rows:
        return "No files found."
    lines = []
    for r in rows[:20]:
        lines.append("  " + " | ".join(str(c) for c in r))
    if len(rows) > 20:
        lines.append(f"  … and {len(rows) - 20} more.")
    return "\n".join(lines)


def _fmt_alerts(rows: list) -> str:
    if not rows:
        return "No alerts found."
    lines = ["ID | Alert For | Type | Similarity | New File | Original | Status"]
    lines.append("-" * 60)
    for r in rows[:20]:
        lines.append(" | ".join(str(c) for c in r))
    if len(rows) > 20:
        lines.append(f"… and {len(rows) - 20} more.")
    return "\n".join(lines)


def _fmt_cross_dups(rows: list) -> str:
    if not rows:
        return "No cross-user duplicate pairs found."
    lines = ["Original File | Downloaded By | Time | Duplicate File | Downloaded By | Time"]
    lines.append("-" * 80)
    for r in rows[:20]:
        lines.append(" | ".join(str(c) for c in r))
    if len(rows) > 20:
        lines.append(f"… and {len(rows) - 20} more.")
    return "\n".join(lines)


# ── Intent detection ──────────────────────────────────────────────────────────

def _detect_intent(text: str) -> str:
    t = text.lower()
    for pattern, intent in _INTENTS:
        if re.search(pattern, t):
            return intent
    return "search"   # default: keyword search


# ── Public API ────────────────────────────────────────────────────────────────

def respond(user_input: str) -> str:
    """
    Process *user_input* and return a human-readable response string.

    The engine tries to identify the intent from natural language, then pulls
    the appropriate query parameters (date range, file type, username, size)
    before hitting the database.
    """
    text = user_input.strip()
    if not text:
        return "Please type a question or command. Type 'help' for guidance."

    intent = _detect_intent(text)

    # ── Simple / fixed intents ────────────────────────────────────────────────
    if intent == "greet":
        return "Hello! I'm the DDAS assistant. Type 'help' to see what I can do."

    if intent == "goodbye":
        return "__EXIT__"

    if intent == "help":
        return _HELP_TEXT

    if intent == "stats":
        s = get_stats()
        return (
            "📊 DDAS Statistics\n"
            f"  Total files tracked : {s['total_files']}\n"
            f"  Total alerts raised : {s['total_alerts']}\n"
            f"  Pending alerts      : {s['pending']}"
        )

    if intent == "alerts":
        rows = get_all_alerts()
        return "🔔 Alerts:\n" + _fmt_alerts(rows)

    if intent == "list_all":
        rows = get_all_downloads()
        return "📁 All downloaded files:\n" + _fmt_files(rows)

    # ── Cross-user duplicates ─────────────────────────────────────────────────
    if intent == "cross_user_dups":
        u1, u2 = _extract_two_users(text)
        if u1 and u2:
            rows = get_cross_user_duplicates(u1, u2)
            return (
                f"🔁 Duplicate files between '{u1}' and '{u2}':\n"
                + _fmt_cross_dups(rows)
            )
        # Might only have one user mentioned
        u1 = _extract_username(text) or ""
        rows = get_cross_user_duplicates(u1)
        label = f"involving '{u1}'" if u1 else "across all users"
        return f"🔁 Cross-user duplicate pairs {label}:\n" + _fmt_cross_dups(rows)

    # ── File-type filter ──────────────────────────────────────────────────────
    if intent == "by_type":
        ftype = _extract_file_type(text)
        if ftype:
            rows = search_files_by_type(ftype)
            return f"📂 Files of type '{ftype.upper()}':\n" + _fmt_files(rows)
        # Fall through to keyword search

    # ── User filter ───────────────────────────────────────────────────────────
    if intent == "by_user":
        username = _extract_username(text)
        if username:
            rows = search_files_by_user(username)
            return f"👤 Files downloaded by '{username}':\n" + _fmt_files(rows)

    # ── Size filter (greater than) ────────────────────────────────────────────
    if intent == "by_size_gt":
        min_bytes = _parse_size_bytes(text)
        if min_bytes is not None:
            rows = search_files_by_size(min_bytes=min_bytes)
            size_label = text  # keep original phrasing for feedback
            return (
                f"📦 Files larger than {min_bytes:,} bytes:\n" + _fmt_files(rows)
            )

    # ── Date filters ──────────────────────────────────────────────────────────
    if intent == "by_date_today":
        start, end = _today_range()
        rows = search_files_by_date_range(start, end)
        return f"📅 Files downloaded today ({start}):\n" + _fmt_files(rows)

    if intent == "by_date_yesterday":
        start, end = _yesterday_range()
        rows = search_files_by_date_range(start, end)
        return f"📅 Files downloaded yesterday ({start}):\n" + _fmt_files(rows)

    if intent == "by_date_week":
        start, end = _this_week_range()
        rows = search_files_by_date_range(start, end)
        return f"📅 Files downloaded this week (since {start}):\n" + _fmt_files(rows)

    if intent == "by_date_month":
        start, end = _this_month_range()
        rows = search_files_by_date_range(start, end)
        return f"📅 Files downloaded this month (since {start}):\n" + _fmt_files(rows)

    if intent == "by_date_last_month":
        start, end = _last_month_range()
        rows = search_files_by_date_range(start, end)
        return f"📅 Files downloaded last month ({start} – {end}):\n" + _fmt_files(rows)

    # ── Default: keyword search (also catches leftover "by_type" / "by_user") ─
    kw = _extract_keyword(text)
    rows = search_files_by_keyword(kw)
    if rows:
        return f"🔍 Results for '{kw}':\n" + _fmt_files(rows)
    return f"No files matched '{kw}'. Try a different keyword or type 'help'."
