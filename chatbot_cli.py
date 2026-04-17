"""
DDAS – Chatbot CLI
Interactive command-line interface for querying DDAS data.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from db.init_db import init_db
from chatbot.chatbot_engine import respond

BANNER = r"""
  ____  ____    _    ____    ____ _           _   _           _
 |  _ \|  _ \  / \  / ___|  / ___| |__   __ _| |_| |__   ___ | |_
 | | | | | | |/ _ \ \___ \ | |   | '_ \ / _` | __| '_ \ / _ \| __|
 | |_| | |_| / ___ \ ___) || |___| | | | (_| | |_| |_) | (_) | |_
 |____/|____/_/   \_\____/  \____|_| |_|\__,_|\__|_.__/ \___/ \__|

  Data Download Duplication Alert System  –  Chatbot Interface
  Type 'help' for commands, 'bye' to exit.
"""


def main() -> None:
    init_db()
    print(BANNER)
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[DDAS] Goodbye!")
            break

        if not user_input:
            continue

        reply = respond(user_input)
        if reply == "__EXIT__":
            print("DDAS: Goodbye! Stay duplicate-free 👋")
            break
        print(f"DDAS: {reply}\n")


if __name__ == "__main__":
    main()
