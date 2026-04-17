"""
DDAS – Chatbot Command-Line Interface

Allows users to query the DDAS system from the terminal.

Usage:
    python chatbot_cli.py
    python chatbot_cli.py --query "show me all pdf files"
    python chatbot_cli.py --user john
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from db import init_db
from chatbot import chatbot_engine
import config


BANNER = """
╔══════════════════════════════════════════════════════╗
║   DDAS Chatbot – Data Download Duplication System   ║
║   Type 'help' for usage  |  Type 'exit' to quit     ║
╚══════════════════════════════════════════════════════╝
"""

HELP_TEXT = """
Commands:
  <any text>   Search local DB (and optionally the web) for matching files
  history      Show your recent chat history
  clear        Clear the screen
  exit / quit  Exit the chatbot
"""


def _show_history(username: str) -> None:
    import sqlite3, os
    if not os.path.isfile(config.DB_PATH):
        print("No history yet.")
        return
    conn = sqlite3.connect(config.DB_PATH)
    rows = conn.execute(
        "SELECT query, response, created_at FROM chat_history WHERE username = ? ORDER BY created_at DESC LIMIT 10",
        (username,),
    ).fetchall()
    conn.close()
    if not rows:
        print("No history yet.")
        return
    for query, response, ts in rows:
        print(f"\n[{ts}] You: {query}")
        print(f"DDAS: {response}")


def run_interactive(username: str) -> None:
    """Start an interactive chatbot session in the terminal."""
    print(BANNER)
    while True:
        try:
            user_input = input(f"[{username}] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        if user_input.lower() == "help":
            print(HELP_TEXT)
            continue
        if user_input.lower() == "history":
            _show_history(username)
            continue
        if user_input.lower() == "clear":
            print("\033[2J\033[H", end="")
            continue

        result = chatbot_engine.ask(user_input, username=username)
        print(f"\n{result['summary']}\n")


def main():
    parser = argparse.ArgumentParser(description="DDAS Chatbot CLI")
    parser.add_argument("--query", "-q", help="Run a single query and exit")
    parser.add_argument("--user", "-u", default="cli_user", help="Username for history tracking")
    args = parser.parse_args()

    init_db.init_database()

    if args.query:
        result = chatbot_engine.ask(args.query, username=args.user)
        print(result["summary"])
    else:
        run_interactive(username=args.user)


if __name__ == "__main__":
    main()
