"""
DDAS – Chatbot Engine
Answers natural-language queries about files stored in the DDAS database.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db.db_helper import search_files_by_keyword, get_all_downloads, get_all_alerts, get_stats


# ── Intent patterns ───────────────────────────────────────────────────────────

_INTENTS: List[tuple[str, str]] = [
    (r"\b(hi|hello|hey)\b",                        "greet"),
    (r"\b(bye|exit|quit|goodbye)\b",               "goodbye"),
    (r"\bhelp\b",                                  "help"),
    (r"\bstats?\b|\b(statistic|summary|count)\b",  "stats"),
    (r"\balerts?\b|\bduplicates?\b|\bwarn\b",      "alerts"),
    # "show all files", "list all downloads", "every file" etc.
    (r"\b(all|every)\b.*\bfiles?\b",               "list_all"),
    (r"\b(show|list)\b.*\b(files?|downloads?)\b",  "list_all"),
    (r"\b(search|find|look|where|who)\b",          "search"),
]

_HELP_TEXT = """
I can answer questions like:
  • "search invoice"          – find files containing 'invoice'
  • "show all files"          – list every downloaded file
  • "show alerts"             – display duplicate alerts
  • "stats"                   – system summary
  • "help"                    – this message
  • "bye"                     – exit the chatbot
""".strip()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _detect_intent(text: str) -> str:
    t = text.lower()
    for pattern, intent in _INTENTS:
        if re.search(pattern, t):
            return intent
    return "search"   # default: treat free text as a keyword search


def _extract_keyword(text: str) -> str:
    """Strip common stop-words and return the most likely search keyword."""
    stop = {"search", "find", "look", "for", "where", "is", "the", "a", "an",
            "show", "me", "please", "file", "download", "any"}
    tokens = [w for w in re.split(r"\W+", text.lower()) if w and w not in stop]
    return " ".join(tokens[:5]) if tokens else text.strip()


def _fmt_files(rows: list) -> str:
    if not rows:
        return "No files found."
    lines = []
    for r in rows[:20]:           # cap output
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


# ── Public API ────────────────────────────────────────────────────────────────

def respond(user_input: str) -> str:
    """
    Process *user_input* and return a human-readable response string.
    """
    text = user_input.strip()
    if not text:
        return "Please type a question or command. Type 'help' for guidance."

    intent = _detect_intent(text)

    if intent == "greet":
        return "Hello! I'm the DDAS assistant. Type 'help' to see what I can do."

    if intent == "goodbye":
        return "__EXIT__"

    if intent == "help":
        return _HELP_TEXT

    if intent == "stats":
        s = get_stats()
        return (
            f"📊 DDAS Statistics\n"
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

    # default: keyword search
    kw = _extract_keyword(text)
    rows = search_files_by_keyword(kw)
    if rows:
        return f"🔍 Results for '{kw}':\n" + _fmt_files(rows)
    return f"No files matched '{kw}'. Try a different keyword or type 'show all files'."
