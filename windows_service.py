"""
windows_service.py – DDAS Windows Service
==========================================
Wraps the DDAS file-monitoring service as a proper Windows service
so it can auto-start on boot and be managed via services.msc / sc.exe.

Requirements:
    pip install pywin32

Installation (run as Administrator):
    python windows_service.py install
    python windows_service.py start
    python windows_service.py stop
    python windows_service.py remove

Or when packaged as an EXE:
    DDAS-Service.exe install
"""

from __future__ import annotations

import os
import sys
import logging
import threading
from pathlib import Path

# Add project root to path so local modules are importable.
sys.path.insert(0, str(Path(__file__).resolve().parent))

SERVICE_NAME = "DDASMonitor"
SERVICE_DISPLAY = "DDAS File Monitor"
SERVICE_DESCRIPTION = (
    "Data Download Duplication Alert System – "
    "real-time duplicate-file detection service."
)

try:
    import win32service
    import win32serviceutil
    import win32event
    import servicemanager
    import win32api
    _HAS_WIN32 = True
except ImportError:
    _HAS_WIN32 = False


# ── Logging ────────────────────────────────────────────────────────────────────
def _get_log_path() -> Path:
    data_root = Path(os.environ.get("PROGRAMDATA", "C:/ProgramData")) / "DDAS"
    data_root.mkdir(parents=True, exist_ok=True)
    return data_root / "service.log"


def _ensure_data_dir_permissions() -> None:
    """
    Grant the built-in *Users* group full control over the DDAS data directory
    so that every Windows user account can read/write the shared database and
    log files without a 'Permission denied' error.

    This is a no-op on non-Windows platforms or when icacls is unavailable.
    """
    if os.name != "nt":
        return
    data_dir = Path(os.environ.get("PROGRAMDATA", "C:/ProgramData")) / "DDAS"
    data_dir.mkdir(parents=True, exist_ok=True)
    try:
        import subprocess as _sp
        _sp.run(
            ["icacls", str(data_dir), "/grant", "Users:(OI)(CI)F", "/T", "/C", "/Q"],
            check=False,
            stdout=_sp.DEVNULL,
            stderr=_sp.DEVNULL,
        )
        log.info("Data directory permissions updated: %s", data_dir)
    except Exception as exc:
        log.warning("Could not set data directory permissions: %s", exc)


logging.basicConfig(
    filename=str(_get_log_path()),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("DDASService")


# ── Service class ──────────────────────────────────────────────────────────────
if _HAS_WIN32:
    class DDASService(win32serviceutil.ServiceFramework):
        """Windows service that runs the DDAS monitor loop."""

        _svc_name_ = SERVICE_NAME
        _svc_display_name_ = SERVICE_DISPLAY
        _svc_description_ = SERVICE_DESCRIPTION

        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self._stop_event = win32event.CreateEvent(None, 0, 0, None)
            self._monitor_thread: threading.Thread | None = None

        def SvcStop(self):
            log.info("Service stop requested.")
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self._stop_event)
            try:
                from ddas_service import stop as monitor_stop
                monitor_stop()
            except Exception as exc:
                log.warning("Error stopping monitor: %s", exc)

        def SvcDoRun(self):
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, ""),
            )
            log.info("DDAS Service starting.")
            self._run()

        def _run(self):
            try:
                from db.init_db import init_db
                _ensure_data_dir_permissions()
                init_db()
                log.info("Database initialised.")

                import ddas_service as svc
                self._monitor_thread = threading.Thread(
                    target=svc.start, daemon=True
                )
                self._monitor_thread.start()
                log.info("Monitor thread started.")

                # Wait until stop is requested
                win32event.WaitForSingleObject(
                    self._stop_event, win32event.INFINITE
                )
                log.info("DDAS Service stopped.")
            except Exception as exc:
                log.exception("Unhandled exception in service: %s", exc)
                self.SvcStop()

else:
    # Provide a stub so the module can be imported on non-Windows systems.
    class DDASService:  # type: ignore[no-redef]
        pass


def _print_usage() -> None:
    print(
        f"DDAS Windows Service Manager\n"
        f"Usage: python {Path(__file__).name} <command>\n\n"
        f"Commands:\n"
        f"  install   Install the service (requires Admin)\n"
        f"  start     Start the service\n"
        f"  stop      Stop the service\n"
        f"  restart   Restart the service\n"
        f"  remove    Uninstall the service\n"
        f"  status    Show service status\n"
        f"  debug     Run the service logic in the console (for testing)\n"
    )


def _debug_run() -> None:
    """Run the monitor in the current console (no Windows service framework)."""
    print("[DEBUG] Running DDAS monitor in debug mode. Press Ctrl+C to stop.")
    from db.init_db import init_db
    import ddas_service as svc
    init_db()
    try:
        svc.start()
    except KeyboardInterrupt:
        print("\n[DEBUG] Stopped.")


def main() -> None:
    if not _HAS_WIN32:
        print(
            "[ERROR] pywin32 is not installed.\n"
            "        Run: pip install pywin32\n"
            "        Then: python pywin32_postinstall.py -install"
        )
        sys.exit(1)

    if len(sys.argv) < 2:
        _print_usage()
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "debug":
        _debug_run()
        return

    if cmd == "status":
        try:
            status = win32serviceutil.QueryServiceStatus(SERVICE_NAME)
            state_map = {
                win32service.SERVICE_STOPPED: "Stopped",
                win32service.SERVICE_START_PENDING: "Starting",
                win32service.SERVICE_STOP_PENDING: "Stopping",
                win32service.SERVICE_RUNNING: "Running",
                win32service.SERVICE_PAUSED: "Paused",
            }
            print(f"Service '{SERVICE_DISPLAY}': {state_map.get(status[1], 'Unknown')}")
        except Exception as exc:
            print(f"Cannot query service: {exc}")
        return

    # Delegate install/start/stop/remove to pywin32's built-in handler
    win32serviceutil.HandleCommandLine(DDASService)


if __name__ == "__main__":
    main()
