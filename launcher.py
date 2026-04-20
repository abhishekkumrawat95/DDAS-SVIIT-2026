"""
launcher.py – DDAS Graphical Launcher
======================================
Provides a friendly Tkinter window that lets the user start/stop
the monitoring service, open the dashboard, or launch the chatbot.
It is also the primary entry-point packaged into DDAS-Launcher.exe.

Enhanced features
-----------------
* Fix Permissions  – grants all Windows users write access to the DDAS
                     data directory so User B can open the app without errors.
* Auto-Start toggle – adds/removes DDAS from the Windows startup registry
                      (HKLM Run) so the monitor launches on every boot.
* Real-time popup alerts – a background thread polls the database every few
                           seconds and shows a desktop notification whenever a
                           new duplicate alert arrives for the current user.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
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
ORANGE = "#fab387"

# How often (ms) to poll for new alerts for the current user
_ALERT_POLL_MS = 4000


# ── Permission helper ─────────────────────────────────────────────────────────

def _fix_data_dir_permissions(data_dir: str) -> bool:
    """
    Use icacls to grant the built-in *Users* group full control over *data_dir*
    (recursive).  Returns True on success, False otherwise.
    Only meaningful on Windows; silently succeeds on other platforms.
    """
    if sys.platform != "win32":
        return True
    try:
        result = subprocess.run(
            ["icacls", data_dir, "/grant", "Users:(OI)(CI)F", "/T", "/C", "/Q"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except Exception:
        return False


# ── Auto-start helpers ────────────────────────────────────────────────────────

def _autostart_exe_path() -> str:
    """Return the path to the launcher executable (or script)."""
    if getattr(sys, "frozen", False):
        return sys.executable          # PyInstaller EXE
    return str(Path(__file__).resolve())


def _is_autostart_enabled() -> bool:
    """Return True if the DDAS auto-start registry entry exists."""
    if sys.platform != "win32":
        return False
    try:
        import winreg
        from config import AUTOSTART_REG_KEY, AUTOSTART_REG_NAME
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, AUTOSTART_REG_KEY)
        winreg.QueryValueEx(key, AUTOSTART_REG_NAME)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def _set_autostart(enabled: bool) -> bool:
    """
    Add or remove the DDAS auto-start registry entry under
    HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run.
    Returns True on success.
    """
    if sys.platform != "win32":
        return False
    try:
        import winreg
        from config import AUTOSTART_REG_KEY, AUTOSTART_REG_NAME
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, AUTOSTART_REG_KEY,
            0, winreg.KEY_SET_VALUE,
        )
        if enabled:
            exe = _autostart_exe_path()
            value = f'"{exe}" monitor'
            winreg.SetValueEx(key, AUTOSTART_REG_NAME, 0, winreg.REG_SZ, value)
        else:
            try:
                winreg.DeleteValue(key, AUTOSTART_REG_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


# ── Alert-polling helpers ─────────────────────────────────────────────────────

def _current_username() -> str:
    """Return the OS username of whoever is running this process."""
    return (
        os.environ.get("USERNAME")
        or os.environ.get("USER")
        or "unknown"
    )


def _show_alert_popup(alert_row: tuple) -> None:
    """
    Show a desktop popup notification for a duplicate-file alert.
    *alert_row* is a row from the alerts table:
        (id, alert_for, duplicate_type, similarity, new_file_name, new_file_path,
         original_file, original_path, original_user, original_time, status, created_time)
    """
    try:
        (
            _id, alert_for, dup_type, similarity,
            new_file, _new_path, orig_file, _orig_path,
            orig_user, _orig_time, _status, _ctime,
        ) = alert_row
        pct = int(float(similarity) * 100)
        msg = (
            f"⚠ Duplicate detected for {alert_for}!\n"
            f"  New file : {new_file}\n"
            f"  Original : {orig_file}  (by {orig_user})\n"
            f"  Match    : {pct}%  [{dup_type}]"
        )
        try:
            from plyer import notification
            notification.notify(
                title="DDAS – Duplicate Alert",
                message=msg,
                timeout=10,
            )
        except Exception:
            pass   # plyer unavailable or headless
    except Exception:
        pass


class LauncherApp(tk.Tk):
    """Main launcher window."""

    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.resizable(False, False)
        self.configure(bg=BG)
        self._monitor_proc: subprocess.Popen | None = None
        self._autostart_var = tk.BooleanVar(value=_is_autostart_enabled())
        self._build_ui()
        # Fix permissions on startup so User B can access shared files
        self._fix_permissions_silent()
        # Start background alert-polling loop
        self._last_seen_alert_id: int = self._get_max_alert_id()
        self._schedule_alert_poll()

    # ── Startup helpers ───────────────────────────────────────────────────────

    def _fix_permissions_silent(self) -> None:
        """Silently attempt to fix DDAS data-dir permissions on startup."""
        if sys.platform != "win32":
            return
        try:
            from config import DATA_DIR
            _fix_data_dir_permissions(str(DATA_DIR))
        except Exception:
            pass

    def _get_max_alert_id(self) -> int:
        """Return the highest alert ID currently in the DB (0 if none)."""
        try:
            from db.db_helper import get_connection
            conn = get_connection()
            row = conn.execute("SELECT MAX(id) FROM alerts").fetchone()
            conn.close()
            return row[0] or 0
        except Exception:
            return 0

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

        tk.Frame(self, bg=PANEL, height=2).pack(fill=tk.X, padx=20, pady=8)

        # Utility buttons
        util_frame = tk.Frame(self, bg=BG)
        util_frame.pack(padx=24, pady=2)
        self._make_btn(
            util_frame, "🔧  Fix Permissions (All Users)",
            self._on_fix_permissions, ORANGE,
        )

        # Auto-start checkbox
        chk_frame = tk.Frame(self, bg=BG)
        chk_frame.pack(pady=(4, 0))
        tk.Checkbutton(
            chk_frame,
            text="Auto-start monitor on Windows boot",
            variable=self._autostart_var,
            command=self._on_autostart_toggle,
            bg=BG, fg=FG,
            activebackground=BG, activeforeground=FG,
            selectcolor=PANEL,
            font=("Segoe UI", 9),
        ).pack()

        tk.Frame(self, bg=PANEL, height=2).pack(fill=tk.X, padx=20, pady=8)

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
            width=30,
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

    # ── Permission fix ────────────────────────────────────────────────────────

    def _on_fix_permissions(self) -> None:
        """Fix DDAS data-dir permissions so all users can access the shared DB."""
        try:
            from config import DATA_DIR
            data_dir = str(DATA_DIR)
        except Exception:
            data_dir = os.path.join(
                os.environ.get("PROGRAMDATA", "C:\\ProgramData"), "DDAS"
            )

        self._log_msg("[INFO] Fixing permissions on: " + data_dir)
        ok = _fix_data_dir_permissions(data_dir)
        if ok:
            self._log_msg("[INFO] Permissions fixed – all users can now access DDAS.")
            messagebox.showinfo(
                "Permissions Fixed",
                f"All users now have full access to:\n{data_dir}\n\n"
                "User B can start DDAS without 'Permission denied' errors.",
            )
        else:
            self._log_msg("[WARN] Could not fix permissions (run as Administrator?).")
            messagebox.showwarning(
                "Permission Fix Failed",
                "Could not update folder permissions.\n\n"
                "Please run DDAS Launcher as Administrator and try again,\n"
                "or run this command manually:\n\n"
                f'icacls "{data_dir}" /grant Users:(OI)(CI)F /T /C',
            )

    # ── Auto-start toggle ─────────────────────────────────────────────────────

    def _on_autostart_toggle(self) -> None:
        enabled = self._autostart_var.get()
        ok = _set_autostart(enabled)
        if ok:
            state = "enabled" if enabled else "disabled"
            self._log_msg(f"[INFO] Auto-start on Windows boot {state}.")
        else:
            # Revert checkbox – operation failed (likely needs admin rights)
            self._autostart_var.set(not enabled)
            self._log_msg("[WARN] Could not update startup registry (run as Administrator?).")
            messagebox.showwarning(
                "Auto-Start Failed",
                "Could not modify the Windows startup registry.\n"
                "Please run DDAS Launcher as Administrator to enable auto-start.",
            )

    # ── Real-time alert polling ───────────────────────────────────────────────

    def _schedule_alert_poll(self) -> None:
        """Schedule the next poll iteration via Tk's after()."""
        self.after(_ALERT_POLL_MS, self._poll_alerts)

    def _poll_alerts(self) -> None:
        """
        Check the database for new alerts directed at the current user that
        have arrived since the last poll.  Show a popup for each one found,
        then mark them as 'shown'.
        """
        try:
            from db.db_helper import get_connection, update_alert_status
            username = _current_username()
            conn = get_connection()
            rows = conn.execute(
                """
                SELECT * FROM alerts
                WHERE  alert_for = ?
                  AND  status    = 'pending'
                  AND  id        > ?
                ORDER  BY id ASC
                """,
                (username, self._last_seen_alert_id),
            ).fetchall()
            conn.close()

            for row in rows:
                alert_id = row[0]
                _show_alert_popup(row)
                # Log to launcher window
                new_file = row[4] if len(row) > 4 else "?"
                orig_file = row[6] if len(row) > 6 else "?"
                self.after(
                    0, self._log_msg,
                    f"[ALERT] Duplicate: '{new_file}' matches '{orig_file}'",
                )
                update_alert_status(alert_id, "shown")
                if alert_id > self._last_seen_alert_id:
                    self._last_seen_alert_id = alert_id

        except Exception:
            pass   # DB not yet initialised or unavailable — silently skip

        self._schedule_alert_poll()

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
