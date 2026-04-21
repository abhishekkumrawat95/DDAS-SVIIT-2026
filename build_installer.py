"""
build_installer.py – Automates the complete DDAS Windows installer build.

Steps performed:
  1. Verify we are on Windows (or allow --force on Linux/macOS for CI).
  2. Check / install PyInstaller.
  3. Run PyInstaller with ddas.spec to produce dist/DDAS/.
  4. Optionally invoke NSIS (makensis) to create dist/DDAS-Setup.exe.
  5. Create a portable ZIP archive at dist/DDAS-Portable.zip.
  6. Print a summary of produced artefacts.

Usage:
    python build_installer.py [--skip-nsis] [--force]
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

# ── Constants ─────────────────────────────────────────────────────────────────
REPO_DIR = Path(__file__).resolve().parent
DIST_DIR = REPO_DIR / "dist"
BUILD_DIR = REPO_DIR / "build"
SPEC_FILE = REPO_DIR / "ddas.spec"
NSI_SCRIPT = REPO_DIR / "installer.nsi"
APP_NAME = "DDAS"
VERSION = "1.0.0"


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    """Run a subprocess command, raising on failure."""
    print(f"\n>>> {' '.join(str(c) for c in cmd)}\n", flush=True)
    result = subprocess.run(cmd, cwd=cwd or REPO_DIR)
    if result.returncode != 0:
        sys.exit(f"[ERROR] Command failed with exit code {result.returncode}")


def check_pyinstaller() -> None:
    """Ensure PyInstaller is importable."""
    try:
        import PyInstaller  # noqa: F401
        print("[OK] PyInstaller is available.")
    except ImportError:
        print("[INFO] PyInstaller not found – installing …")
        _run([sys.executable, "-m", "pip", "install", "pyinstaller"])


def build_executables() -> None:
    """Run PyInstaller to produce the dist/DDAS folder."""
    print("\n" + "=" * 60)
    print("  Building executables with PyInstaller …")
    print("  NOTE: First-run collection of large packages (transformers,")
    print("        sklearn, scipy …) can take 10–30 minutes.  The terminal")
    print("        will show per-package progress — it is NOT frozen.")
    print("=" * 60, flush=True)
    _run([
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(SPEC_FILE),
    ])
    print("\n[OK] PyInstaller build complete.")


def build_nsis_installer() -> None:
    """Invoke makensis to produce DDAS-Setup.exe."""
    makensis = shutil.which("makensis")
    if not makensis:
        # Common NSIS install location on Windows (e.g., winget default).
        default_nsis = Path(r"C:\Program Files (x86)\NSIS\makensis.exe")
        if default_nsis.exists():
            makensis = str(default_nsis)

    if not makensis:
        print("[WARN] makensis not found in PATH – skipping NSIS build.")
        print("       Install NSIS from https://nsis.sourceforge.io/ and re-run.")
        return

    print("\n" + "=" * 60)
    print("  Building NSIS installer …")
    print("=" * 60)
    _run([makensis, str(NSI_SCRIPT)])
    installer_path = DIST_DIR / "DDAS-Setup.exe"
    if installer_path.exists():
        print(f"[OK] Installer created: {installer_path}")
    else:
        print("[WARN] makensis ran but DDAS-Setup.exe was not found.")


def create_portable_zip() -> None:
    """Zip dist/DDAS into dist/DDAS-Portable.zip."""
    ddas_folder = DIST_DIR / "DDAS"
    if not ddas_folder.is_dir():
        print("[WARN] dist/DDAS folder not found – skipping portable ZIP.")
        return

    zip_path = DIST_DIR / "DDAS-Portable.zip"
    print(f"\n[INFO] Creating portable archive: {zip_path}")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in ddas_folder.rglob("*"):
            zf.write(file, Path("DDAS") / file.relative_to(ddas_folder))

    size_mb = zip_path.stat().st_size / 1_048_576
    print(f"[OK]  DDAS-Portable.zip created ({size_mb:.1f} MB)")


def copy_readme() -> None:
    """Copy a quick-start README into dist/."""
    readme_src = REPO_DIR / "INSTALLATION_GUIDE.md"
    readme_dst = DIST_DIR / "README.txt"
    if readme_src.exists():
        shutil.copy2(readme_src, readme_dst)
        print(f"[OK] README copied to {readme_dst}")


def print_summary() -> None:
    """List all artefacts in dist/."""
    print("\n" + "=" * 60)
    print("  Build summary")
    print("=" * 60)
    if DIST_DIR.is_dir():
        for item in sorted(DIST_DIR.iterdir()):
            if item.is_file():
                size_mb = item.stat().st_size / 1_048_576
                print(f"  {item.name:<35} {size_mb:>8.1f} MB")
            else:
                print(f"  {item.name}/  (folder)")
    print("\nDone! ✓")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build DDAS Windows installer")
    parser.add_argument("--skip-nsis", action="store_true",
                        help="Skip NSIS installer step")
    parser.add_argument("--force", action="store_true",
                        help="Run on non-Windows platforms (for CI)")
    args = parser.parse_args()

    if sys.platform != "win32" and not args.force:
        sys.exit(
            "[ERROR] This script targets Windows.\n"
            "        Add --force to run on Linux/macOS (useful in CI)."
        )

    check_pyinstaller()
    build_executables()

    if not args.skip_nsis:
        build_nsis_installer()

    create_portable_zip()
    copy_readme()
    print_summary()


if __name__ == "__main__":
    main()
