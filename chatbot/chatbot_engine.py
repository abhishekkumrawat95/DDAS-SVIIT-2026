"""
DDAS – Chatbot Engine
Answers user queries by searching the local DDAS database and the web.
"""

import re
import sys
import os
from typing import Dict, List, Optional

# Allow direct import from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import db_helper


# ---------------------------------------------------------------------------
# Online search (DuckDuckGo Instant Answer API – no API key required)
# ---------------------------------------------------------------------------

def search_online(query: str, max_results: int = 3) -> List[Dict]:
    """
    Fetch results from DuckDuckGo Instant Answer API.
    Returns a list of {'title': ..., 'snippet': ..., 'url': ...} dicts.
    Falls back gracefully when the network is unavailable.
    """
    results = []
    try:
        import urllib.request
        import urllib.parse
        import json

        params = urllib.parse.urlencode({
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
        })
        url = f"https://api.duckduckgo.com/?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "DDAS-Chatbot/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        # Abstract (best single answer)
        if data.get("AbstractText"):
            results.append({
                "title": data.get("Heading", query),
                "snippet": data["AbstractText"],
                "url": data.get("AbstractURL", ""),
            })

        # Related topics
        for topic in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({
                    "title": topic.get("Text", "")[:80],
                    "snippet": topic.get("Text", ""),
                    "url": topic.get("FirstURL", ""),
                })
            if len(results) >= max_results:
                break
    except Exception:
        pass
    return results


# ---------------------------------------------------------------------------
# Local database helpers
# ---------------------------------------------------------------------------

def search_local(keyword: str) -> List[Dict]:
    """Search the DDAS downloads table by keyword."""
    rows = db_helper.search_files_by_keyword(keyword)
    return [
        {
            "file_name": r[0],
            "file_path": r[1],
            "user": r[2],
            "download_time": r[3],
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Simple intent / keyword extraction
# ---------------------------------------------------------------------------

_GREETINGS = re.compile(r"\b(hi|hello|hey|greetings|namaste)\b", re.I)
_FAREWELL  = re.compile(r"\b(bye|exit|quit|goodbye|see you)\b", re.I)
_HELP      = re.compile(r"\b(help|what can you do|commands|how)\b", re.I)
_STATS     = re.compile(r"\b(stats|statistics|summary|count|total|how many)\b", re.I)
_ALERTS    = re.compile(r"\b(alert|alerts|duplicate|duplicates|warning)\b", re.I)


def _extract_search_terms(text: str) -> str:
    """Strip common question words and return the core search phrase."""
    stop = r"\b(is|there|any|a|an|the|file|for|on|in|about|do|does|have|has|i|me|my|please|can|you|tell|find|search|show|list|get)\b"
    cleaned = re.sub(stop, " ", text, flags=re.I)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ?!.,")
    return cleaned


# ---------------------------------------------------------------------------
# Main chatbot processor
# ---------------------------------------------------------------------------

HELP_TEXT = """I can help you with:
  • Searching files in the local DDAS database
    → e.g. "is Q1_Sales_Report.xlsx here?"
  • Checking for duplicates / alerts
    → e.g. "show alerts" or "any duplicates?"
  • Database statistics
    → e.g. "how many files are downloaded?"
  • Searching the web for any topic
    → e.g. "search online for Python tutorials"
  • Type 'bye' to exit."""


def process_query(user_input: str) -> str:
    """
    Main entry-point.
    Accepts a natural-language string and returns a formatted response.
    """
    text = user_input.strip()
    if not text:
        return "Please type a question or command."

    # ---- greetings ----------------------------------------------------------
    if _GREETINGS.search(text):
        return "Hello! I'm the DDAS Chatbot. How can I help you today?\n" + HELP_TEXT

    # ---- farewell -----------------------------------------------------------
    if _FAREWELL.search(text):
        return "Goodbye! Stay duplicate-free! 👋"

    # ---- help ---------------------------------------------------------------
    if _HELP.search(text):
        return HELP_TEXT

    # ---- statistics ---------------------------------------------------------
    if _STATS.search(text):
        return _get_stats()

    # ---- alerts / duplicates ------------------------------------------------
    if _ALERTS.search(text):
        return _get_recent_alerts()

    # ---- explicit online search ---------------------------------------------
    online_forced = re.search(
        r"\b(search online|google|search web|web search|internet)\b", text, re.I
    )
    if online_forced:
        query = re.sub(
            r"\b(search online for|google|search web for|search web|web search|search the web for|internet)\b",
            "", text, flags=re.I
        ).strip()
        return _online_response(query or text)

    # ---- local search first, fall back to online ----------------------------
    search_terms = _extract_search_terms(text)
    local_results = search_local(search_terms) if search_terms else []

    if local_results:
        return _format_local_results(search_terms, local_results)

    # Nothing found locally – try online
    online_results = search_online(search_terms or text)
    if online_results:
        return _format_online_results(search_terms or text, online_results)

    return (
        f"I couldn't find '{search_terms}' in the local database or online. "
        "Try a different keyword or phrase."
    )


# ---------------------------------------------------------------------------
# Response formatters
# ---------------------------------------------------------------------------

def _get_stats() -> str:
    downloads = db_helper.get_all_downloads()
    alerts = db_helper.get_alerts_for_user("") if hasattr(db_helper, "get_all_alerts") else []
    # Use get_all_downloads as proxy for total files
    total_files = len(downloads)
    lines = [f"📊 DDAS Statistics", f"  Total files tracked : {total_files}"]
    if hasattr(db_helper, "get_all_alerts"):
        lines.append(f"  Pending alerts       : {len(alerts)}")
    return "\n".join(lines)


def _get_recent_alerts() -> str:
    # Get all pending alerts (alert_for='') not supported directly – show all
    try:
        conn = db_helper.get_connection()
        rows = conn.execute(
            "SELECT id, duplicate_type, new_file_name, original_file, status, created_at "
            "FROM alerts ORDER BY id DESC LIMIT 10"
        ).fetchall()
        conn.close()
    except Exception:
        return "Could not retrieve alerts from the database."

    if not rows:
        return "✅ No alerts found. No duplicates detected yet."

    lines = ["🔔 Recent Alerts (last 10):"]
    for row in rows:
        aid, dtype, new_f, orig_f, status, created = row
        lines.append(
            f"  [{aid}] {dtype} | {new_f} ↔ {orig_f} | {status} | {created}"
        )
    return "\n".join(lines)


def _format_local_results(keyword: str, results: List[Dict]) -> str:
    lines = [f"✅ Found {len(results)} result(s) in local database for '{keyword}':"]
    for r in results[:10]:
        lines.append(
            f"  • {r['file_name']} | by {r['user']} on {r['download_time']}"
        )
        lines.append(f"    Path: {r['file_path']}")
    return "\n".join(lines)


def _format_online_results(query: str, results: List[Dict]) -> str:
    lines = [f"🌐 Online results for '{query}':"]
    for r in results:
        lines.append(f"  • {r['title']}")
        if r.get("snippet") and r["snippet"] != r["title"]:
            snippet = r["snippet"][:200]
            lines.append(f"    {snippet}")
        if r.get("url"):
            lines.append(f"    🔗 {r['url']}")
    return "\n".join(lines)


def _online_response(query: str) -> str:
    results = search_online(query)
    if results:
        return _format_online_results(query, results)
    return f"No online results found for '{query}'."
