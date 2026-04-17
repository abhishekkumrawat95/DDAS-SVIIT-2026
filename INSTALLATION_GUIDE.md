# DDAS – Installation Guide

> **Data Download Duplication Alert System**  
> Version 1.0.0 | SVIIT Minor Project 2026

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Quick Install (Recommended)](#quick-install-recommended)
3. [Step-by-Step Installation Wizard](#step-by-step-installation-wizard)
4. [First Launch](#first-launch)
5. [Using the Application](#using-the-application)
6. [Portable Version](#portable-version)
7. [Windows Service (Auto-start)](#windows-service-auto-start)
8. [Uninstalling DDAS](#uninstalling-ddas)
9. [Troubleshooting](#troubleshooting)

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10 (64-bit) | Windows 11 (64-bit) |
| RAM | 512 MB free | 2 GB free |
| Disk | 400 MB | 1 GB |
| Permissions | Standard user | Administrator (for service install) |
| Python | **Not required** | – |

> **No Python installation is required.** All dependencies are bundled inside
> the installer.

---

## Quick Install (Recommended)

1. **Download** `DDAS-Setup.exe` from the releases page.
2. **Double-click** `DDAS-Setup.exe`.
3. Click **Next** through the wizard and accept the defaults.
4. Click **Install**.
5. Once finished, click **Finish** – DDAS Launcher opens automatically.

---

## Step-by-Step Installation Wizard

### Step 1 – Run the installer

Double-click `DDAS-Setup.exe`. If Windows Defender SmartScreen appears, click
**"More info" → "Run anyway"**. The installer requires administrator rights to
write to `Program Files`.

### Step 2 – License / readme

Read the quick-start information and click **Next**.

### Step 3 – Choose installation folder

The default is `C:\Program Files\DDAS`. You can change this, but keep the
path free of spaces for best compatibility.

### Step 4 – Optional: Windows Service

Tick **"Install as Windows Service (auto-start on boot)"** if you want the
file monitor to start automatically every time the computer boots. This
requires administrator rights and installs the service under the name
`DDASMonitor`.

### Step 5 – Install

Click **Install** and wait (~30 seconds). A progress bar will track the copy
of files.

### Step 6 – Finish

Click **Finish**. A desktop shortcut and Start Menu folder are created.

---

## First Launch

After installation, open **DDAS Launcher** from:
- The **Desktop** shortcut, or
- **Start Menu → DDAS → DDAS Launcher**

The launcher window looks like this:

```
┌─────────────────────────────────────────────────────┐
│  🗂  DDAS Launcher                                  │
│  Data Download Duplication Alert System  v1.0.0     │
│─────────────────────────────────────────────────────│
│  [ ▶  Start Monitor  ]                              │
│  [ ■  Stop Monitor   ]  (disabled until started)   │
│  [ 📊  Open Dashboard ]                             │
│  [ 🤖  Open Chatbot  ]                              │
│─────────────────────────────────────────────────────│
│  Monitor status:  Stopped                           │
│                                                     │
│  Log:                                               │
│  ┌─────────────────────────────────────────────┐   │
│  │                                             │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

Click **▶ Start Monitor** to begin watching your Downloads folder for
duplicate files.

---

## Using the Application

### Monitoring service

- **Start Monitor** – begins watching the configured folder (default:
  `%USERPROFILE%\Downloads`) in the background.
- **Stop Monitor** – gracefully stops the watcher.

### Dashboard

Click **📊 Open Dashboard** to open the Tkinter analytics window. It shows:
- Number of files monitored
- Duplicate groups found
- Recent alerts

### Chatbot

Click **🤖 Open Chatbot** to open an interactive console where you can ask
questions like:

```
> show duplicates
> list alerts
> how many files today
> help
```

---

## Portable Version

If you downloaded `DDAS-Portable.zip`:

1. Extract the ZIP to any folder (e.g. `D:\DDAS`).
2. Open the extracted `DDAS\` folder.
3. Double-click **`DDAS-Launcher.exe`**.

No installation or administrator rights are needed for the portable version.
User data is still saved to `%PROGRAMDATA%\DDAS\`.

---

## Windows Service (Auto-start)

To make the monitor start automatically on boot without logging in:

```
# Run Command Prompt as Administrator
DDAS-Monitor.exe install
DDAS-Monitor.exe start
```

Manage the service:

```
DDAS-Monitor.exe stop
DDAS-Monitor.exe restart
DDAS-Monitor.exe remove
```

Or use **Services** (`services.msc`) – look for **"DDAS File Monitor"**.

---

## Uninstalling DDAS

### Via Control Panel

1. Open **Settings → Apps → Installed apps**.
2. Search for **DDAS**.
3. Click the three-dot menu → **Uninstall**.

### Via Start Menu

**Start → DDAS → Uninstall DDAS**

### Via Command Line

```
"C:\Program Files\DDAS\Uninstall DDAS.exe"
```

> **Note:** Uninstalling removes program files and shortcuts. Your database
> and logs in `%PROGRAMDATA%\DDAS` are **preserved** by default.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Installer blocked by SmartScreen | Click "More info" → "Run anyway" |
| "Access denied" error | Right-click installer → "Run as administrator" |
| Monitor doesn't detect files | Check the watched folder in the Dashboard settings |
| Dashboard doesn't open | Ensure DDAS-Dashboard.exe is in the same folder as the Launcher |
| Chatbot shows import error | Re-install DDAS; some files may be corrupted |
| Service fails to start | Check `%PROGRAMDATA%\DDAS\service.log` for details |
| Antivirus flags DDAS-*.exe | Add an exclusion for `C:\Program Files\DDAS\` |

For further help, open an issue at:  
https://github.com/abhishekkumrawat95/DDAS-SVIIT-2026/issues
