"""
DDAS – Tkinter Dashboard
Shows download history, duplicate alerts, and live statistics.
"""

from __future__ import annotations

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox

sys.path.insert(0, os.path.dirname(__file__))

from db.init_db import init_db
from db.db_helper import get_all_downloads, get_all_alerts, get_stats, update_alert_status
from config import DASHBOARD_REFRESH_MS as REFRESH_MS


class DDASDashboard(tk.Tk):
    """Main dashboard window."""

    def __init__(self) -> None:
        super().__init__()
        self.title("DDAS – Data Download Duplication Alert System")
        self.geometry("1000x620")
        self.resizable(True, True)
        self.configure(bg="#1e1e2e")
        self._build_ui()
        self.refresh()
        self._schedule_refresh()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # Header
        hdr = tk.Label(
            self, text="📁  DDAS Dashboard",
            font=("Helvetica", 18, "bold"),
            bg="#1e1e2e", fg="#cdd6f4",
        )
        hdr.pack(pady=(12, 4))

        # Stats bar
        self._stats_var = tk.StringVar(value="Loading…")
        tk.Label(
            self, textvariable=self._stats_var,
            font=("Helvetica", 10),
            bg="#1e1e2e", fg="#a6e3a1",
        ).pack(pady=(0, 8))

        # Notebook (tabs)
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        self._files_tab  = self._build_tree_tab(nb, "Downloads",
            ("File Name", "Type", "User", "Downloaded At", "Path"),
            col_widths=(220, 60, 100, 160, 360),
        )
        self._alerts_tab = self._build_tree_tab(nb, "Alerts",
            ("ID", "Alert For", "Type", "Similarity", "New File", "Original", "Status"),
            col_widths=(40, 100, 100, 80, 180, 180, 80),
        )

        nb.add(self._files_tab,  text="📥 Downloaded Files")
        nb.add(self._alerts_tab, text="🔔 Duplicate Alerts")

        # Button bar
        btn_frame = tk.Frame(self, bg="#1e1e2e")
        btn_frame.pack(fill=tk.X, padx=12, pady=6)

        for text, cmd in [
            ("⟳ Refresh",        self.refresh),
            ("✔ Mark Resolved",   self._resolve_alert),
            ("✖ Quit",            self.destroy),
        ]:
            tk.Button(
                btn_frame, text=text, command=cmd,
                bg="#313244", fg="#cdd6f4",
                relief=tk.FLAT, padx=10, pady=4,
            ).pack(side=tk.LEFT, padx=4)

    @staticmethod
    def _build_tree_tab(
        parent: ttk.Notebook,
        name: str,
        columns: tuple,
        col_widths: tuple,
    ) -> tk.Frame:
        frame = tk.Frame(parent, bg="#1e1e2e")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=20)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
            background="#181825", foreground="#cdd6f4",
            rowheight=24, fieldbackground="#181825",
        )
        style.configure("Treeview.Heading",
            background="#313244", foreground="#cdd6f4", font=("Helvetica", 9, "bold"),
        )
        style.map("Treeview", background=[("selected", "#45475a")])

        for col, w in zip(columns, col_widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor=tk.W)

        vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL,   command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        # Store tree reference in frame for later access
        frame._tree = tree  # type: ignore[attr-defined]
        return frame

    # ── Data refresh ──────────────────────────────────────────────────────────

    def refresh(self) -> None:
        """Reload data from DB in a background thread."""
        threading.Thread(target=self._load_data, daemon=True).start()

    def _load_data(self) -> None:
        try:
            stats   = get_stats()
            files   = get_all_downloads()
            alerts  = get_all_alerts()
        except Exception as exc:
            self.after(0, lambda: self._stats_var.set(f"Error: {exc}"))
            return
        self.after(0, lambda: self._update_ui(stats, files, alerts))

    def _update_ui(self, stats: dict, files: list, alerts: list) -> None:
        self._stats_var.set(
            f"Files: {stats['total_files']}   |   "
            f"Alerts: {stats['total_alerts']}   |   "
            f"Pending: {stats['pending']}"
        )
        self._populate_tree(self._files_tab._tree, files)   # type: ignore[attr-defined]
        self._populate_tree(self._alerts_tab._tree, alerts)  # type: ignore[attr-defined]

    @staticmethod
    def _populate_tree(tree: ttk.Treeview, rows: list) -> None:
        tree.delete(*tree.get_children())
        for row in rows:
            tree.insert("", tk.END, values=row)

    def _schedule_refresh(self) -> None:
        self.after(REFRESH_MS, self._auto_refresh)

    def _auto_refresh(self) -> None:
        self.refresh()
        self._schedule_refresh()

    # ── Alert actions ─────────────────────────────────────────────────────────

    def _resolve_alert(self) -> None:
        tree = self._alerts_tab._tree  # type: ignore[attr-defined]
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("DDAS", "Select an alert row first.")
            return
        for item in sel:
            row = tree.item(item, "values")
            if row:
                alert_id = int(row[0])
                update_alert_status(alert_id, "resolved")
        self.refresh()


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    init_db()
    app = DDASDashboard()
    app.mainloop()


if __name__ == "__main__":
    main()
