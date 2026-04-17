"""
launcher.py – DDAS Graphical Launcher
======================================
Provides a friendly Tkinter window that lets the user start/stop
the monitoring service, open the dashboard, or launch the chatbot.
It is also the primary entry-point packaged into DDAS-Launcher.exe.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
from pathlib import Path

# When running from a PyInstaller bundle, sys._MEIPASS is the temp extraction
# folder.  We add it (or the script directory) to the path so local modules
# resolve correctly.
_BASE = getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)
sys.path.insert(0, str(_BASE))

APP_NAME = "DDAS – Data Download Duplication Alert System"
VERSION = "1.0.0"

# Colours (Catppuccin-inspired palette, same as the Tkinter dashboard)
BG     = "#1e1e2e"
PANEL  = "#313244"
FG     = "#cdd6f4"
ACCENT = "#89b4fa"
GREEN  = "#a6e3a1"
RED    = "#f38ba8"
YELLOW = "#f9e2af"


class LauncherApp(tk.Tk):
    """Main launcher window."""

    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.resizable(False, False)
        self.configure(bg=BG)
        self._monitor_proc: subprocess.Popen | None = None
        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # Title bar
        tk.Label(
            self, text="🗂  DDAS Launcher", font=("Segoe UI", 16, "bold"),
            bg=BG, fg=ACCENT,
        ).pack(pady=(18, 4))
        tk.Label(
            self, text=f"Data Download Duplication Alert System  v{VERSION}",
            font=("Segoe UI", 9), bg=BG, fg=FG,
        ).pack()

        tk.Frame(self, bg=PANEL, height=2).pack(fill=tk.X, padx=20, pady=12)

        # Module buttons
        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.pack(padx=24, pady=4)

        self._btn_monitor = self._make_btn(
            btn_frame, "▶  Start Monitor", self._start_monitor, GREEN)
        self._btn_stop = self._make_btn(
            btn_frame, "■  Stop Monitor", self._stop_monitor, RED)
        self._btn_stop.config(state=tk.DISABLED)
        self._make_btn(btn_frame, "📊  Open Dashboard", self._open_dashboard, ACCENT)
        self._make_btn(btn_frame, "🤖  Open Chatbot", self._open_chatbot, YELLOW)

        tk.Frame(self, bg=PANEL, height=2).pack(fill=tk.X, padx=20, pady=12)

        # Status indicator
        status_row = tk.Frame(self, bg=BG)
        status_row.pack()
        tk.Label(status_row, text="Monitor status:", bg=BG, fg=FG,
                 font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 6))
        self._status_var = tk.StringVar(value="Stopped")
        self._status_lbl = tk.Label(
            status_row, textvariable=self._status_var,
            bg=BG, fg=RED, font=("Segoe UI", 9, "bold"))
        self._status_lbl.pack(side=tk.LEFT)

        # Log output
        tk.Label(self, text="Log:", bg=BG, fg=FG,
                 font=("Segoe UI", 9)).pack(anchor=tk.W, padx=24)
        self._log = scrolledtext.ScrolledText(
            self, width=62, height=10,
            bg=PANEL, fg=FG, insertbackground=FG,
            font=("Consolas", 8), state=tk.DISABLED, relief=tk.FLAT,
        )
        self._log.pack(padx=20, pady=(2, 12))

        # Footer
        tk.Label(
            self, text="© 2026 DDAS Team – SVIIT",
            font=("Segoe UI", 7), bg=BG, fg="#585b70",
        ).pack(pady=(0, 10))

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    @staticmethod
    def _make_btn(parent: tk.Widget, text: str, cmd, fg: str) -> tk.Button:
        btn = tk.Button(
            parent, text=text, command=cmd,
            bg=PANEL, fg=fg,
            activebackground=BG, activeforeground=fg,
            relief=tk.FLAT, padx=12, pady=6,
            font=("Segoe UI", 9),
            width=22,
        )
        btn.pack(pady=3, fill=tk.X)
        return btn

    # ── Logging ───────────────────────────────────────────────────────────────

    def _log_msg(self, msg: str) -> None:
        self._log.config(state=tk.NORMAL)
        self._log.insert(tk.END, msg + "\n")
        self._log.see(tk.END)
        self._log.config(state=tk.DISABLED)

    # ── Monitor control ───────────────────────────────────────────────────────

    def _start_monitor(self) -> None:
        if self._monitor_proc and self._monitor_proc.poll() is None:
            self._log_msg("[WARN] Monitor is already running.")
            return

        exe = self._resolve_exe("DDAS-Monitor", "main.py")
        try:
            cmd = (
                [sys.executable, exe, "monitor"]
                if exe.endswith(".py")
                else [exe, "monitor"]
            )
            self._monitor_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            self._status_var.set("Running")
            self._status_lbl.config(fg=GREEN)
            self._btn_monitor.config(state=tk.DISABLED)
            self._btn_stop.config(state=tk.NORMAL)
            self._log_msg("[INFO] Monitor started (PID %d)." % self._monitor_proc.pid)
            threading.Thread(target=self._tail_monitor, daemon=True).start()
        except FileNotFoundError as exc:
            messagebox.showerror("Error", f"Cannot start monitor:\n{exc}")

    def _tail_monitor(self) -> None:
        """Read monitor stdout in a background thread and feed it to the log."""
        if not self._monitor_proc:
            return
        for line in self._monitor_proc.stdout:
            self.after(0, self._log_msg, line.decode(errors="replace").rstrip())
        self.after(0, self._on_monitor_exit)

    def _on_monitor_exit(self) -> None:
        self._status_var.set("Stopped")
        self._status_lbl.config(fg=RED)
        self._btn_monitor.config(state=tk.NORMAL)
        self._btn_stop.config(state=tk.DISABLED)
        self._log_msg("[INFO] Monitor process exited.")

    def _stop_monitor(self) -> None:
        if self._monitor_proc and self._monitor_proc.poll() is None:
            self._monitor_proc.terminate()
            self._log_msg("[INFO] Monitor stop requested.")
        else:
            self._log_msg("[WARN] Monitor is not running.")

    # ── Dashboard / Chatbot launchers ─────────────────────────────────────────

    def _open_dashboard(self) -> None:
        exe = self._resolve_exe("DDAS-Dashboard", "ddas_dashboard.py")
        try:
            cmd = [sys.executable, exe] if exe.endswith(".py") else [exe]
            subprocess.Popen(cmd)
            self._log_msg("[INFO] Dashboard launched.")
        except FileNotFoundError as exc:
            messagebox.showerror("Error", f"Cannot open dashboard:\n{exc}")

    def _open_chatbot(self) -> None:
        exe = self._resolve_exe("DDAS-Chatbot", "chatbot_cli.py")
        try:
            if exe.endswith(".py"):
                # Open a new console window for the chatbot CLI
                if sys.platform == "win32":
                    subprocess.Popen(
                        ["cmd", "/c", "start", "cmd", "/k",
                         sys.executable, exe],
                        shell=True,
                    )
                else:
                    subprocess.Popen([sys.executable, exe])
            else:
                if sys.platform == "win32":
                    subprocess.Popen(
                        ["cmd", "/c", "start", "", exe],
                        shell=True,
                    )
                else:
                    subprocess.Popen([exe])
            self._log_msg("[INFO] Chatbot launched.")
        except FileNotFoundError as exc:
            messagebox.showerror("Error", f"Cannot open chatbot:\n{exc}")

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _resolve_exe(exe_name: str, fallback_script: str) -> str:
        """
        Return path to the compiled executable when running from a bundle,
        or fall back to the Python source script.
        """
        # When bundled by PyInstaller all EXEs live next to each other
        bundle_dir = Path(sys.executable).parent
        for candidate in (
            bundle_dir / f"{exe_name}.exe",
            bundle_dir / exe_name,
        ):
            if candidate.exists():
                return str(candidate)
        # Development fallback
        return str(Path(__file__).resolve().parent / fallback_script)

    def _on_close(self) -> None:
        if self._monitor_proc and self._monitor_proc.poll() is None:
            if messagebox.askyesno(
                "Quit", "Monitor is still running. Stop it and quit?"
            ):
                self._stop_monitor()
                self.destroy()
        else:
            self.destroy()


def main() -> None:
    app = LauncherApp()
    app.mainloop()


if __name__ == "__main__":
    main()
