# DDAS – Deployment Guide

> End-to-end instructions for packaging, distributing, and deploying DDAS
> to Windows desktops and organisations.

---

## Deployment Scenarios

| Scenario | Recommended Package | Notes |
|----------|--------------------|-------|
| Single home PC | `DDAS-Setup.exe` | Double-click to install |
| No-install / USB drive | `DDAS-Portable.zip` | Extract and run |
| Corporate managed (GPO/SCCM) | `DDAS-Setup.exe /S` | Silent install flag |
| Organisation with auto-monitor | Windows Service install | Starts on boot |

---

## Preparing the Distribution Package

### Build all artefacts

```batch
build.bat
```

After a successful build you will find:

```
dist\
├── DDAS-Setup.exe       ← Share with end-users
├── DDAS-Portable.zip    ← Portable option
└── README.txt           ← Quick-start guide
```

### Verify the build

```batch
dist\DDAS\DDAS-Launcher.exe
```

Confirm the Launcher window opens and each module starts correctly.

---

## Distribution Methods

### GitHub Releases

1. Tag the commit:
   ```
   git tag v1.0.0
   git push origin v1.0.0
   ```
2. On GitHub, create a new Release from the tag.
3. Upload `DDAS-Setup.exe`, `DDAS-Portable.zip`, and `README.txt` as release
   assets.
4. Users download directly from the release page.

### USB / Shared Drive

Copy `DDAS-Setup.exe` (or the portable ZIP) to a USB drive or shared network
folder. Users double-click to install or run portably.

### Email / File Transfer

Attach `DDAS-Setup.exe` to an email or upload to a file-sharing service.  
> Note: Some email providers block `.exe` attachments. Rename to `.exe.zip`
> or share via Google Drive / OneDrive.

### Software Centre / SCCM

Use the silent install flag:

```batch
DDAS-Setup.exe /S
```

To install to a custom folder:

```batch
DDAS-Setup.exe /S /D=C:\Tools\DDAS
```

---

## Post-Installation Configuration

### Default watch folder

DDAS monitors `%USERPROFILE%\Downloads` by default.  
Change this via the Dashboard → Settings, or set the environment variable
before starting the monitor:

```
set DDAS_WATCH_FOLDER=D:\SharedDownloads
DDAS-Monitor.exe monitor
```

### Email notifications

Set the following environment variables (or edit `.env` in the data folder):

```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASS=yourpassword
NOTIFY_EMAIL=alerts@yourcompany.com
```

### Windows Service for automatic startup

Run once as Administrator after installation:

```
"C:\Program Files\DDAS\DDAS-Monitor.exe" install
"C:\Program Files\DDAS\DDAS-Monitor.exe" start
```

The service (`DDASMonitor`) now starts automatically on every boot.

---

## Updating DDAS

### Via installer (recommended)

Run the new `DDAS-Setup.exe`. It overwrites the existing installation while
preserving the database and logs.

### Manual update

1. Stop the service (if running): `sc stop DDASMonitor`
2. Replace the contents of `C:\Program Files\DDAS\` with the new `dist\DDAS\` folder.
3. Restart the service: `sc start DDASMonitor`

---

## Data Locations

| Item | Path |
|------|------|
| SQLite database | `%PROGRAMDATA%\DDAS\ddas.db` |
| Application log | `%PROGRAMDATA%\DDAS\ddas.log` |
| Service log | `%PROGRAMDATA%\DDAS\service.log` |

These locations are **not** removed during an uninstall, preserving user data.

---

## Security Considerations

- DDAS runs under the **logged-in user's** account (or SYSTEM when installed
  as a Windows service).
- The SQLite database is stored in `%PROGRAMDATA%\DDAS` – ensure appropriate
  NTFS permissions are applied in multi-user environments.
- SMTP credentials are stored as plain-text environment variables. Use a
  dedicated app password or an email relay for production deployments.
- Optionally sign `DDAS-Setup.exe` and the individual EXEs with a
  **code-signing certificate** to avoid SmartScreen warnings.

---

## Rollback

To revert to a previous version:

1. Uninstall the current version: `"C:\Program Files\DDAS\Uninstall DDAS.exe"`
2. Install the previous release's `DDAS-Setup.exe`.

The database at `%PROGRAMDATA%\DDAS\ddas.db` is schema-forward-compatible
between releases.

---

## Support and Issue Tracking

- GitHub Issues: <https://github.com/abhishekkumrawat95/DDAS-SVIIT-2026/issues>
- Logs: `%PROGRAMDATA%\DDAS\ddas.log`
