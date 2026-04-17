"""
DDAS – Main Application Orchestrator
Provides a unified entry-point for all DDAS components.

Usage:
    python main.py monitor    – start file monitoring service
    python main.py dashboard  – launch Tkinter dashboard
    python main.py chatbot    – interactive chatbot CLI
    python main.py tray       – system-tray icon (start monitor + tray)
    python main.py init       – initialize / reset the database only
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from db.init_db import init_db


def _usage() -> None:
    print(__doc__)
    sys.exit(1)


def main() -> None:
    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else ""

    if cmd == "init":
        init_db()
        print("[DDAS] Database initialized.")

    elif cmd == "monitor":
        init_db()
        from ddas_service import start
        folder = sys.argv[2] if len(sys.argv) > 2 else None
        start(folder) if folder else start()

    elif cmd == "dashboard":
        init_db()
        from ddas_dashboard import main as dash_main
        dash_main()

    elif cmd == "chatbot":
        init_db()
        from chatbot_cli import main as chat_main
        chat_main()

    elif cmd == "tray":
        from ddas_tray import main as tray_main
        tray_main()

    else:
        _usage()


if __name__ == "__main__":
    main()
