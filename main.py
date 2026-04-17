"""
DDAS – Application Entry Point

Starts the Monitor Service and System Tray in parallel threads,
then launches the Tkinter Dashboard on the main thread.

Usage:
    python main.py [--service-only] [--tray-only] [--dashboard-only]
"""

import argparse
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from db import init_db


def _run_service():
    from ddas_service import run_service
    run_service()


def _run_tray():
    from ddas_tray import run_tray
    run_tray()


def _run_dashboard():
    from ddas_dashboard import run_dashboard
    run_dashboard()


def main():
    parser = argparse.ArgumentParser(description="DDAS – Data Download Duplication Alert System")
    parser.add_argument("--service-only", action="store_true", help="Run monitor service only")
    parser.add_argument("--tray-only", action="store_true", help="Run system tray only")
    parser.add_argument("--dashboard-only", action="store_true", help="Run dashboard only")
    args = parser.parse_args()

    # Always initialise the database on startup
    init_db.init_database()

    if args.service_only:
        _run_service()
        return

    if args.tray_only:
        _run_tray()
        return

    if args.dashboard_only:
        _run_dashboard()
        return

    # Default: start service + tray in background, dashboard on main thread
    service_thread = threading.Thread(target=_run_service, daemon=True, name="ddas-service")
    tray_thread = threading.Thread(target=_run_tray, daemon=True, name="ddas-tray")

    service_thread.start()
    tray_thread.start()

    _run_dashboard()


if __name__ == "__main__":
    main()
