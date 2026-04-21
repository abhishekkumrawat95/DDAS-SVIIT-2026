# -*- mode: python ; coding: utf-8 -*-
"""
ddas.spec – PyInstaller specification file for DDAS
Builds three separate executables that share the same collected data:
  • DDAS-Launcher.exe  (GUI launcher – the primary user-facing executable)
  • DDAS-Monitor.exe   (file-monitoring service, no console window)
  • DDAS-Dashboard.exe (Tkinter dashboard)
  • DDAS-Chatbot.exe   (interactive chatbot, console window)

Run with:
    pyinstaller ddas.spec
or use build_installer.py which calls this automatically.
"""

import sys
from PyInstaller.utils.hooks import collect_all, collect_submodules

# ── Collect third-party packages that have data files ────────────────────────
# NOTE: collect_all() on large packages (transformers, sklearn, scipy) can take
#       several minutes — this is normal.  Progress is printed below.
datas_all = []
binaries_all = []
hiddenimports_all = []

_COLLECT_PKGS = (
    "watchdog", "sklearn", "scipy", "PIL", "cv2", "pystray",
    "plyer", "transformers", "tokenizers", "huggingface_hub",
    "safetensors", "regex", "tqdm", "numpy", "ImageHash",
    "PyWavelets",
)

print(f"\n[spec] Collecting data/hooks for {len(_COLLECT_PKGS)} packages …", flush=True)
print("[spec] NOTE: Each large package (transformers, sklearn, scipy …) can take",
      flush=True)
print("[spec]       several minutes.  The build is NOT frozen – please be patient.",
      flush=True)

for _pkg in _COLLECT_PKGS:
    print(f"[spec]   • {_pkg} …", end=" ", flush=True)
    try:
        d, b, h = collect_all(_pkg)
        datas_all += d
        binaries_all += b
        hiddenimports_all += h
        print(f"ok ({len(d)} data, {len(b)} bin, {len(h)} hidden)", flush=True)
    except Exception as _exc:
        print(f"skipped ({_exc})", flush=True)

print("[spec] Package collection complete.\n", flush=True)

# Additional hidden imports for dynamic loading patterns used in the app
hiddenimports_extra = [
    # stdlib / tkinter
    "tkinter",
    "tkinter.ttk",
    "tkinter.messagebox",
    "tkinter.filedialog",
    "tkinter.scrolledtext",
    # DB / detection / chatbot sub-packages
    "db",
    "db.db_helper",
    "db.init_db",
    "detection",
    "detection.hash_engine",
    "detection.text_similarity",
    "detection.image_video_detect",
    "chatbot",
    "chatbot.chatbot_engine",
    # scikit-learn internals
    "sklearn.utils._cython_blas",
    "sklearn.neighbors.typedefs",
    "sklearn.neighbors.quad_tree",
    "sklearn.tree._utils",
    # scipy
    "scipy.special.cython_special",
    # PIL
    "PIL._tkinter_finder",
    # Windows-only (safe to list even if unused on other platforms)
    "win32api",
    "win32con",
    "win32service",
    "win32serviceutil",
    "win32event",
    "servicemanager",
    "pywintypes",
]
hiddenimports_all += hiddenimports_extra

# ── Shared Analysis ───────────────────────────────────────────────────────────
# We analyse launcher.py; the other entry-points are collected as pure scripts
# so they share the same dependency graph (smaller total on-disk size).

a = Analysis(
    ["launcher.py"],
    pathex=["."],
    binaries=binaries_all,
    datas=datas_all,
    hiddenimports=hiddenimports_all,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "PyQt5", "PyQt6", "PySide2", "PySide6",
              "IPython", "jupyter"],
    noarchive=False,
    optimize=0,
)

a_monitor = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=binaries_all,
    datas=datas_all,
    hiddenimports=hiddenimports_all,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "PyQt5", "PyQt6", "PySide2", "PySide6",
              "IPython", "jupyter"],
    noarchive=False,
    optimize=0,
)

a_chatbot = Analysis(
    ["chatbot_cli.py"],
    pathex=["."],
    binaries=binaries_all,
    datas=datas_all,
    hiddenimports=hiddenimports_all,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "PyQt5", "PyQt6", "PySide2", "PySide6",
              "IPython", "jupyter"],
    noarchive=False,
    optimize=0,
)

a_dashboard = Analysis(
    ["ddas_dashboard.py"],
    pathex=["."],
    binaries=binaries_all,
    datas=datas_all,
    hiddenimports=hiddenimports_all,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "PyQt5", "PyQt6", "PySide2", "PySide6",
              "IPython", "jupyter"],
    noarchive=False,
    optimize=0,
)

# ── Merge shared files to avoid duplication ───────────────────────────────────
MERGE(
    (a,           "DDAS-Launcher",   "DDAS-Launcher"),
    (a_monitor,   "DDAS-Monitor",    "DDAS-Monitor"),
    (a_chatbot,   "DDAS-Chatbot",    "DDAS-Chatbot"),
    (a_dashboard, "DDAS-Dashboard",  "DDAS-Dashboard"),
)

# ── PYZ archives ──────────────────────────────────────────────────────────────
pyz          = PYZ(a.pure)
pyz_monitor  = PYZ(a_monitor.pure)
pyz_chatbot  = PYZ(a_chatbot.pure)
pyz_dashboard = PYZ(a_dashboard.pure)

# ── Executables ───────────────────────────────────────────────────────────────
exe_launcher = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DDAS-Launcher",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # GUI app – no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=None,              # replace with "assets/ddas.ico" if you have one
)

exe_monitor = EXE(
    pyz_monitor,
    a_monitor.scripts,
    [],
    exclude_binaries=True,
    name="DDAS-Monitor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=None,
)

exe_chatbot = EXE(
    pyz_chatbot,
    a_chatbot.scripts,
    [],
    exclude_binaries=True,
    name="DDAS-Chatbot",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,           # chatbot needs a console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=None,
)

exe_dashboard = EXE(
    pyz_dashboard,
    a_dashboard.scripts,
    [],
    exclude_binaries=True,
    name="DDAS-Dashboard",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=None,
)

# ── One-folder collection (all four exes share the same _MEIPASS) ─────────────
coll = COLLECT(
    exe_launcher,   a.binaries,   a.datas,
    exe_monitor,    a_monitor.binaries,   a_monitor.datas,
    exe_chatbot,    a_chatbot.binaries,   a_chatbot.datas,
    exe_dashboard,  a_dashboard.binaries, a_dashboard.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="DDAS",
)
