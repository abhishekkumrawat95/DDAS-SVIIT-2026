"""
DDAS – Chatbot CLI
Interactive command-line interface for the DDAS chatbot.
Usage:  python chatbot_cli.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.init_db import init_database
from chatbot.chatbot_engine import process_query

BANNER = r"""
  ____  ____    _    ____     ____ _           _   _           _
 |  _ \|  _ \  / \  / ___|   / ___| |__   __ _| |_| |__   ___ | |_
 | | | | | | |/ _ \ \___ \  | |   | '_ \ / _` | __| '_ \ / _ \| __|
 | |_| | |_| / ___ \ ___) | | |___| | | | (_| | |_| |_) | (_) | |_
 |____/|____/_/   \_\____/   \____|_| |_|\__,_|\__|_.__/ \___/ \__|

  Data Download Duplication Alert System – Chatbot
  Type 'help' for commands, 'bye' to exit.
"""


def main():
    init_database()
    print(BANNER)

    while True:
        try:
            user_input = input("\n🤖 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        response = process_query(user_input)
        print(f"\n💬 DDAS: {response}\n")

        if user_input.lower() in ("bye", "exit", "quit"):
            break


if __name__ == "__main__":
    main()
