"""
DDAS – Tkinter Dashboard
Displays recent downloads, duplicate alerts, and basic statistics.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import db_helper
from db.init_db import init_database


# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
BG_DARK   = "#1e1e2e"
BG_PANEL  = "#2a2a3c"
BG_ROW    = "#2f2f42"
FG_WHITE  = "#cdd6f4"
FG_ACCENT = "#89b4fa"
FG_GREEN  = "#a6e3a1"
FG_RED    = "#f38ba8"
FG_YELLOW = "#f9e2af"
FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_HEAD  = ("Segoe UI", 11, "bold")
FONT_BODY  = ("Segoe UI", 10)


class DDASDashboard(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("DDAS – Data Download Duplication Alert System")
        self.geometry("1100x680")
        self.configure(bg=BG_DARK)
        self.resizable(True, True)

        # Apply a dark ttk theme where possible
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        self._apply_styles(style)

        self._build_header()
        self._build_notebook()
        self._build_status_bar()

        self.after(500, self.refresh_all)
        self.after(30_000, self._auto_refresh)  # refresh every 30 seconds

    # ------------------------------------------------------------------
    # Style helpers
    # ------------------------------------------------------------------

    def _apply_styles(self, style: ttk.Style):
        style.configure("TNotebook", background=BG_DARK, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=BG_PANEL, foreground=FG_WHITE,
            padding=[12, 6], font=FONT_BODY,
        )
        style.map("TNotebook.Tab", background=[("selected", FG_ACCENT)])
        style.configure(
            "Treeview",
            background=BG_ROW, fieldbackground=BG_ROW,
            foreground=FG_WHITE, rowheight=24, font=FONT_BODY,
        )
        style.configure(
            "Treeview.Heading",
            background=BG_PANEL, foreground=FG_ACCENT, font=FONT_HEAD,
        )
        style.map("Treeview", background=[("selected", FG_ACCENT)])

    # ------------------------------------------------------------------
    # Layout builders
    # ------------------------------------------------------------------

    def _build_header(self):
        hdr = tk.Frame(self, bg=BG_PANEL, pady=10)
        hdr.pack(fill="x")
        tk.Label(
            hdr, text="🛡  DDAS Dashboard", font=FONT_TITLE,
            bg=BG_PANEL, fg=FG_ACCENT,
        ).pack(side="left", padx=20)
        tk.Button(
            hdr, text="⟳ Refresh", command=self.refresh_all,
            bg=FG_ACCENT, fg=BG_DARK, font=FONT_BODY, relief="flat", padx=10,
        ).pack(side="right", padx=10)

    def _build_notebook(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        self._tab_overview(nb)
        self._tab_downloads(nb)
        self._tab_alerts(nb)
        self._tab_search(nb)

    def _build_status_bar(self):
        self._status_var = tk.StringVar(value="Ready")
        bar = tk.Label(
            self, textvariable=self._status_var,
            bg=BG_PANEL, fg=FG_WHITE, font=FONT_BODY, anchor="w", padx=10,
        )
        bar.pack(fill="x", side="bottom")

    # ------------------------------------------------------------------
    # Tab: Overview
    # ------------------------------------------------------------------

    def _tab_overview(self, nb: ttk.Notebook):
        frame = tk.Frame(nb, bg=BG_DARK)
        nb.add(frame, text=" Overview ")

        from typing import Dict
        self._overview_stats: Dict[str, tk.StringVar] = {}
        stats = [
            ("total_files",   "📁 Total Files",    FG_GREEN),
            ("total_alerts",  "🔔 Total Alerts",   FG_YELLOW),
            ("pending_alerts","⚠️  Pending Alerts", FG_RED),
        ]
        cards = tk.Frame(frame, bg=BG_DARK)
        cards.pack(pady=30)
        for key, label, colour in stats:
            var = tk.StringVar(value="–")
            self._overview_stats[key] = var
            card = tk.Frame(cards, bg=BG_PANEL, padx=30, pady=20, bd=1, relief="ridge")
            card.pack(side="left", padx=15)
            tk.Label(card, text=label, bg=BG_PANEL, fg=FG_WHITE, font=FONT_BODY).pack()
            tk.Label(card, textvariable=var, bg=BG_PANEL, fg=colour,
                     font=("Segoe UI", 28, "bold")).pack()

    def _refresh_overview(self):
        downloads = db_helper.get_all_downloads()
        self._overview_stats["total_files"].set(str(len(downloads)))
        try:
            conn = db_helper.get_connection()
            total = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
            pending = conn.execute(
                "SELECT COUNT(*) FROM alerts WHERE status='pending'"
            ).fetchone()[0]
            conn.close()
        except Exception:
            total, pending = 0, 0
        self._overview_stats["total_alerts"].set(str(total))
        self._overview_stats["pending_alerts"].set(str(pending))

    # ------------------------------------------------------------------
    # Tab: Downloads
    # ------------------------------------------------------------------

    def _tab_downloads(self, nb: ttk.Notebook):
        frame = tk.Frame(nb, bg=BG_DARK)
        nb.add(frame, text=" Downloads ")

        cols = ("File Name", "Type", "User", "Downloaded At", "Path")
        self._dl_tree = self._make_tree(frame, cols)

    def _refresh_downloads(self):
        self._dl_tree.delete(*self._dl_tree.get_children())
        for row in db_helper.get_all_downloads():
            self._dl_tree.insert("", "end", values=row)

    # ------------------------------------------------------------------
    # Tab: Alerts
    # ------------------------------------------------------------------

    def _tab_alerts(self, nb: ttk.Notebook):
        frame = tk.Frame(nb, bg=BG_DARK)
        nb.add(frame, text=" Alerts ")

        btn_frame = tk.Frame(frame, bg=BG_DARK)
        btn_frame.pack(fill="x", padx=5, pady=5)
        tk.Button(
            btn_frame, text="✔ Mark Selected Resolved",
            command=self._resolve_selected_alert,
            bg=FG_GREEN, fg=BG_DARK, font=FONT_BODY, relief="flat", padx=10,
        ).pack(side="left", padx=5)

        cols = ("ID", "Type", "New File", "Original File", "Similarity %", "Status", "Created")
        self._al_tree = self._make_tree(frame, cols)

    def _refresh_alerts(self):
        self._al_tree.delete(*self._al_tree.get_children())
        try:
            conn = db_helper.get_connection()
            rows = conn.execute(
                "SELECT id, duplicate_type, new_file_name, original_file, "
                "similarity, status, created_at FROM alerts ORDER BY id DESC"
            ).fetchall()
            conn.close()
        except Exception:
            rows = []
        for row in rows:
            tag = "pending" if row[5] == "pending" else "resolved"
            self._al_tree.insert("", "end", values=row, tags=(tag,))
        self._al_tree.tag_configure("pending", foreground=FG_YELLOW)
        self._al_tree.tag_configure("resolved", foreground=FG_GREEN)

    def _resolve_selected_alert(self):
        sel = self._al_tree.selection()
        if not sel:
            messagebox.showinfo("DDAS", "Select an alert first.")
            return
        for item in sel:
            alert_id = self._al_tree.item(item)["values"][0]
            db_helper.update_alert_status(alert_id, "resolved")
        self._refresh_alerts()
        self._status_var.set(f"Resolved {len(sel)} alert(s).")

    # ------------------------------------------------------------------
    # Tab: Search
    # ------------------------------------------------------------------

    def _tab_search(self, nb: ttk.Notebook):
        frame = tk.Frame(nb, bg=BG_DARK)
        nb.add(frame, text=" Search ")

        search_row = tk.Frame(frame, bg=BG_DARK)
        search_row.pack(fill="x", padx=10, pady=10)

        self._search_var = tk.StringVar()
        entry = tk.Entry(search_row, textvariable=self._search_var,
                         font=FONT_BODY, width=50, bg=BG_PANEL, fg=FG_WHITE,
                         insertbackground=FG_WHITE)
        entry.pack(side="left", padx=5)
        entry.bind("<Return>", lambda _e: self._do_search())
        tk.Button(
            search_row, text="Search", command=self._do_search,
            bg=FG_ACCENT, fg=BG_DARK, font=FONT_BODY, relief="flat", padx=10,
        ).pack(side="left", padx=5)

        cols = ("File Name", "Path", "User", "Downloaded At")
        self._sr_tree = self._make_tree(frame, cols)

    def _do_search(self):
        keyword = self._search_var.get().strip()
        if not keyword:
            return
        self._sr_tree.delete(*self._sr_tree.get_children())
        rows = db_helper.search_files_by_keyword(keyword)
        for row in rows:
            self._sr_tree.insert("", "end", values=row)
        self._status_var.set(f"Found {len(rows)} result(s) for '{keyword}'")

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _make_tree(self, parent, columns) -> ttk.Treeview:
        container = tk.Frame(parent, bg=BG_DARK)
        container.pack(fill="both", expand=True, padx=5, pady=5)

        vsb = ttk.Scrollbar(container, orient="vertical")
        hsb = ttk.Scrollbar(container, orient="horizontal")
        tree = ttk.Treeview(
            container, columns=columns, show="headings",
            yscrollcommand=vsb.set, xscrollcommand=hsb.set,
        )
        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=160, minwidth=80)

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        return tree

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def refresh_all(self):
        self._refresh_overview()
        self._refresh_downloads()
        self._refresh_alerts()
        self._status_var.set(f"Last refreshed: {datetime.now().strftime('%H:%M:%S')}")

    def _auto_refresh(self):
        self.refresh_all()
        self.after(30_000, self._auto_refresh)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    init_database()
    app = DDASDashboard()
    app.mainloop()


if __name__ == "__main__":
    main()
