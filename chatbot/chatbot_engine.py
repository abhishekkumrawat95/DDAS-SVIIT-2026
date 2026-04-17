"""
DDAS – Chatbot Engine
Answers user queries by searching the local DDAS database and (optionally)
performing an online search via DuckDuckGo Lite.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

from db import db_helper


def _search_local(keyword: str) -> List[Dict[str, Any]]:
    """Search the local DDAS database for files matching *keyword*."""
    rows = db_helper.search_files_by_keyword(keyword)
    results = []
    for row in rows:
        file_name, file_path, downloaded_by, download_time = row
        results.append({
            "source": "local",
            "file_name": file_name,
            "file_path": file_path,
            "downloaded_by": downloaded_by,
            "download_time": download_time,
        })
    return results


def _search_online(keyword: str, max_results: int = config.ONLINE_SEARCH_MAX_RESULTS) -> List[Dict[str, Any]]:
    """
    Query DuckDuckGo Lite for *keyword* and return a list of result dicts.
    Returns an empty list if the request fails or online search is disabled.
    """
    if not config.ONLINE_SEARCH_ENABLED:
        return []
    try:
        import httpx
        url = "https://lite.duckduckgo.com/lite/"
        headers = {"User-Agent": "DDAS-Chatbot/1.0"}
        resp = httpx.post(url, data={"q": keyword}, headers=headers, timeout=10)
        resp.raise_for_status()

        import re
        links = re.findall(r'<a[^>]+href="(https?://[^"]+)"[^>]*>([^<]+)</a>', resp.text)
        results = []
        for href, title in links[:max_results]:
            results.append({
                "source": "online",
                "title": title.strip(),
                "url": href,
            })
        return results
    except Exception:
        return []


def _save_history(username: str, query: str, response: str, source: str) -> None:
    """Persist a chat interaction to the database."""
    try:
        import sqlite3, os
        os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
        conn = sqlite3.connect(config.DB_PATH)
        conn.execute("""
            INSERT INTO chat_history (username, query, response, source)
            VALUES (?, ?, ?, ?)
        """, (username, query, response, source))
        conn.commit()
        conn.close()
    except Exception:
        pass


def ask(query: str, username: str = "guest") -> Dict[str, Any]:
    """
    Handle a natural-language query.

    Returns a dict with:
        - query        : the original query
        - local_results: list of matching files from the local DB
        - online_results: list of web results (empty if disabled)
        - summary      : human-readable answer string
    """
    keyword = query.strip()
    local = _search_local(keyword)
    online = _search_online(keyword)

    # Build a human-readable summary
    lines = []

    if local:
        lines.append(f"Found {len(local)} file(s) in the local database matching '{keyword}':")
        for item in local:
            lines.append(
                f"  • {item['file_name']} — downloaded by {item['downloaded_by']} on {item['download_time']}"
            )
    else:
        lines.append(f"No files found in the local database matching '{keyword}'.")

    if config.ONLINE_SEARCH_ENABLED:
        if online:
            lines.append(f"\nOnline results for '{keyword}':")
            for item in online:
                lines.append(f"  • {item['title']}: {item['url']}")
        else:
            lines.append("\nNo online results found (or online search failed).")

    summary = "\n".join(lines)
    source = "local+online" if online else "local"
    _save_history(username, query, summary, source)

    return {
        "query": query,
        "local_results": local,
        "online_results": online,
        "summary": summary,
    }
