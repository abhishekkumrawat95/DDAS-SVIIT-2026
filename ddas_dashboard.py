"""
DDAS – Tkinter Dashboard
Provides a simple GUI to view downloads, alerts, and interact with the chatbot.
"""

import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config
from db import db_helper
from chatbot import chatbot_engine

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
    _TK_AVAILABLE = True
except ImportError:
    _TK_AVAILABLE = False

import os

USERNAME = os.getenv("USERNAME") or os.getenv("USER") or "unknown"


class DDASApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DDAS – Data Download Duplication Alert System")
        self.geometry("900x600")
        self.resizable(True, True)
        self._build_ui()
        self._refresh()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self._tab_downloads = self._make_downloads_tab(notebook)
        self._tab_alerts = self._make_alerts_tab(notebook)
        self._tab_chatbot = self._make_chatbot_tab(notebook)

        notebook.add(self._tab_downloads, text="  Downloads  ")
        notebook.add(self._tab_alerts, text="  Alerts  ")
        notebook.add(self._tab_chatbot, text="  Chatbot  ")

        # Status bar
        self._status = tk.StringVar(value="Ready")
        tk.Label(self, textvariable=self._status, anchor=tk.W, relief=tk.SUNKEN).pack(
            fill=tk.X, side=tk.BOTTOM
        )

    def _make_downloads_tab(self, parent) -> tk.Frame:
        frame = tk.Frame(parent)
        cols = ("File Name", "Type", "Downloaded By", "Date/Time", "Path")
        tree = ttk.Treeview(frame, columns=cols, show="headings")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=160 if col != "Path" else 260)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._downloads_tree = tree
        btn = tk.Button(frame, text="⟳ Refresh", command=self._load_downloads)
        btn.pack(side=tk.BOTTOM, pady=4)
        return frame

    def _make_alerts_tab(self, parent) -> tk.Frame:
        frame = tk.Frame(parent)
        cols = ("ID", "Alert For", "Type", "New File", "Original File", "Similarity", "Status")
        tree = ttk.Treeview(frame, columns=cols, show="headings")
        widths = [40, 100, 80, 200, 200, 80, 80]
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._alerts_tree = tree
        btn_frame = tk.Frame(frame)
        btn_frame.pack(side=tk.BOTTOM, pady=4)
        tk.Button(btn_frame, text="⟳ Refresh", command=self._load_alerts).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="✔ Mark Resolved", command=self._resolve_alert).pack(side=tk.LEFT, padx=4)
        return frame

    def _make_chatbot_tab(self, parent) -> tk.Frame:
        frame = tk.Frame(parent)
        self._chat_display = scrolledtext.ScrolledText(frame, wrap=tk.WORD, state=tk.DISABLED, height=25)
        self._chat_display.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        entry_frame = tk.Frame(frame)
        entry_frame.pack(fill=tk.X, padx=4, pady=(0, 4))
        self._chat_entry = tk.Entry(entry_frame, font=("Segoe UI", 11))
        self._chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._chat_entry.bind("<Return>", lambda _e: self._send_message())
        tk.Button(entry_frame, text="Send", command=self._send_message).pack(side=tk.LEFT, padx=4)
        return frame

    # ── Data Loading ──────────────────────────────────────────────────────────

    def _refresh(self):
        self._load_downloads()
        self._load_alerts()
        self.after(config.SCAN_INTERVAL * 1000, self._refresh)

    def _load_downloads(self):
        for row in self._downloads_tree.get_children():
            self._downloads_tree.delete(row)
        try:
            for row in db_helper.get_all_downloads():
                self._downloads_tree.insert("", tk.END, values=row)
            self._status.set("Downloads loaded.")
        except Exception as exc:
            self._status.set(f"Error loading downloads: {exc}")

    def _load_alerts(self):
        for row in self._alerts_tree.get_children():
            self._alerts_tree.delete(row)
        try:
            import sqlite3
            conn = sqlite3.connect(config.DB_PATH)
            rows = conn.execute(
                "SELECT id, alert_for, duplicate_type, new_file_name, original_file, similarity, status FROM alerts ORDER BY id DESC"
            ).fetchall()
            conn.close()
            for row in rows:
                self._alerts_tree.insert("", tk.END, values=row)
            self._status.set("Alerts loaded.")
        except Exception as exc:
            self._status.set(f"Error loading alerts: {exc}")

    def _resolve_alert(self):
        selected = self._alerts_tree.selection()
        if not selected:
            messagebox.showinfo("DDAS", "Please select an alert to resolve.")
            return
        item = self._alerts_tree.item(selected[0])
        alert_id = item["values"][0]
        db_helper.update_alert_status(int(alert_id), "resolved")
        self._load_alerts()

    # ── Chatbot ───────────────────────────────────────────────────────────────

    def _send_message(self):
        query = self._chat_entry.get().strip()
        if not query:
            return
        self._chat_entry.delete(0, tk.END)
        self._append_chat(f"You: {query}\n")
        threading.Thread(target=self._ask_chatbot, args=(query,), daemon=True).start()

    def _ask_chatbot(self, query: str):
        result = chatbot_engine.ask(query, username=USERNAME)
        self.after(0, self._append_chat, f"DDAS: {result['summary']}\n\n")

    def _append_chat(self, text: str):
        self._chat_display.configure(state=tk.NORMAL)
        self._chat_display.insert(tk.END, text)
        self._chat_display.see(tk.END)
        self._chat_display.configure(state=tk.DISABLED)


def run_dashboard():
    if not _TK_AVAILABLE:
        print("[DDAS Dashboard] tkinter not available in this environment.")
        return
    app = DDASApp()
    app.mainloop()


if __name__ == "__main__":
    run_dashboard()
