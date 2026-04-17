# DDAS – Build Guide

> How to build the **DDAS-Setup.exe** Windows installer from source.

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.10+ | Running PyInstaller and the build script |
| pip | latest | Installing Python packages |
| NSIS | 3.x | Creating the Setup.exe installer wizard |
| UPX *(optional)* | 4.x | Compressing executables (reduces size ~30%) |

### Install Python

Download from <https://www.python.org/downloads/windows/>.  
During setup tick **"Add Python to PATH"**.

### Install NSIS

Download the installer from <https://nsis.sourceforge.io/Download>.  
After installation, ensure `makensis.exe` is on your `PATH`:

```
makensis --version
```

### Install UPX (optional)

Download from <https://upx.github.io/> and place `upx.exe` on your `PATH`:

```
upx --version
```

---

## Quick Build (one command)

Open a Command Prompt in the project root and run:

```batch
build.bat
```

This script will:
1. Create/activate a Python virtual environment (`.venv`).
2. Install all dependencies from `requirements.txt`.
3. Run `build_installer.py` which calls PyInstaller then NSIS.
4. Produce `dist\DDAS-Setup.exe` and `dist\DDAS-Portable.zip`.

---

## Manual Build Steps

### Step 1 – Install dependencies

```batch
pip install -r requirements.txt
```

### Step 2 – Build executables with PyInstaller

```batch
pyinstaller --clean --noconfirm ddas.spec
```

This produces:
```
dist\DDAS\
├── DDAS-Launcher.exe
├── DDAS-Monitor.exe
├── DDAS-Dashboard.exe
├── DDAS-Chatbot.exe
└── _internal\          ← shared libraries
```

### Step 3 – Create the Setup.exe with NSIS

```batch
makensis installer.nsi
```

This produces `dist\DDAS-Setup.exe`.

### Step 4 – Create the portable ZIP

```batch
python -c "
import zipfile, pathlib
z = pathlib.Path('dist/DDAS-Portable.zip')
with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
    for f in pathlib.Path('dist/DDAS').rglob('*'):
        zf.write(f, pathlib.Path('DDAS') / f.relative_to('dist/DDAS'))
print('Created', z)
"
```

---

## Output Structure

After a successful build, the `dist\` folder contains:

```
dist\
├── DDAS-Setup.exe       ← Windows installer (share with users)
├── DDAS-Portable.zip    ← Portable archive (no install needed)
├── README.txt           ← Quick-start guide
└── DDAS\                ← Raw PyInstaller output
    ├── DDAS-Launcher.exe
    ├── DDAS-Monitor.exe
    ├── DDAS-Dashboard.exe
    ├── DDAS-Chatbot.exe
    └── _internal\
```

---

## Customising the Build

### Changing the version number

Edit the `VERSION` constant near the top of `build_installer.py` and the
`!define PRODUCT_VERSION` line in `installer.nsi`.

### Adding an application icon

1. Place a `ddas.ico` file in the project root (or an `assets/` subfolder).
2. In `ddas.spec`, change `icon=None` to `icon="ddas.ico"` for each `EXE()`.
3. In `installer.nsi`, uncomment the `Icon` line and point it at the `.ico`.

### Reducing bundle size

- Ensure UPX is on PATH (PyInstaller uses it automatically when `upx=True`).
- Add unnecessary packages to the `excludes` list in `ddas.spec`.
- Use `--strip` flag (Linux/macOS only).

### One-file mode

If you prefer a single-file EXE (slower startup, larger file):
- Change `exclude_binaries=True` → `exclude_binaries=False` for each `EXE`.
- Remove the `COLLECT()` block.
- Add `a.binaries` and `a.datas` into each `EXE()`.

---

## CI / Automated Builds

To build from a GitHub Actions workflow (Windows runner):

```yaml
jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - run: python build_installer.py --skip-nsis
      - uses: actions/upload-artifact@v4
        with:
          name: DDAS-dist
          path: dist/
```

---

## Troubleshooting Builds

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError` during PyInstaller | Add the module to `hiddenimports` in `ddas.spec` |
| Missing DLL at runtime | Add the DLL to the `binaries` list in `ddas.spec` |
| `makensis: command not found` | Install NSIS and add to PATH; or run with `--skip-nsis` |
| Large bundle size | Enable UPX; add unused packages to `excludes` |
| Anti-virus false positive | Sign the EXEs with a code-signing certificate |
