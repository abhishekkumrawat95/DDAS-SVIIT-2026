# DDAS – Data Download Duplication Alert System

**SVIIT Minor Project 2026**

---

## Project Overview

DDAS prevents redundant downloads on a shared PC by detecting duplicate files
the moment they are saved to a monitored folder.  It supports three kinds of
duplicate checks:

| Check | Technique | File types |
|-------|-----------|------------|
| Exact duplicate | SHA-256 hash | All |
| Near-duplicate text | TF-IDF cosine similarity | PDF, DOCX, TXT, … |
| Similar image/video | Perceptual hash (pHash) | JPG, PNG, MP4, … |

---

## Project Structure

```
DDAS-SVIIT-2026/
├── ddas_service.py        ← Watchdog file-monitoring service
├── ddas_tray.py           ← System-tray icon + desktop notifications
├── ddas_dashboard.py      ← Tkinter dashboard UI
├── chatbot_cli.py         ← Interactive chatbot CLI
│
├── detection/
│   ├── hash_engine.py         SHA-256 / MD5 hashing
│   ├── text_similarity.py     TF-IDF near-duplicate text detection
│   └── image_video_detect.py  pHash for images and videos
│
├── chatbot/
│   └── chatbot_engine.py      Chatbot: local DB + DuckDuckGo online search
│
└── db/
    ├── db_helper.py           SQLite CRUD helpers
    └── init_db.py             Schema creation + default config
```

---

## Tech Stack

- **Python 3.11+**
- **Watchdog** – real-time filesystem events
- **pystray / plyer** – system-tray icon and desktop notifications
- **Pillow / ImageHash** – perceptual hashing for images
- **OpenCV** – video frame sampling
- **scikit-learn** – TF-IDF text similarity
- **Tkinter** – built-in dashboard UI
- **SQLite** – embedded database (no server required)

---

## Team

| Role | Member |
|------|--------|
| Leader / Project Management | Abhishek Kumrawat |
| Database / Backend | Member 2 |
| Notifications / Chatbot | Member 3 |
| Dashboard UI | Member 4 |

---

## Setup Instructions

```bash
# 1. Clone
git clone https://github.com/abhishekkumrawat95/DDAS-SVIIT-2026.git
cd DDAS-SVIIT-2026

# 2. Create virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialise database (creates ~/.ddas/ddas.db)
python db/init_db.py
```

---

## Running the System

### File Monitoring Service
```bash
# Watch the default Downloads folder
python ddas_service.py

# Watch specific folders
python ddas_service.py /home/user/Documents /home/user/Downloads
```

### Tkinter Dashboard
```bash
python ddas_dashboard.py
```

### System Tray (background monitoring + notifications)
```bash
python ddas_tray.py
```

### Chatbot CLI
```bash
python chatbot_cli.py
```
Then ask questions like:
- `is Q1_Sales_Report.xlsx downloaded?`
- `show alerts`
- `how many files are tracked?`
- `search online for Python tutorials`

---

## Database

The SQLite database is stored at `~/.ddas/ddas.db` (cross-platform).

Tables:

| Table | Purpose |
|-------|---------|
| `downloads` | Every tracked file with hash, metadata, extracted text |
| `alerts` | Duplicate detection alerts |
| `configurations` | System settings (thresholds, email, etc.) |

---

## Configuration

Edit the `configurations` table or modify constants at the top of each module:

| Setting | Default | Location |
|---------|---------|----------|
| Text similarity threshold | 0.75 (75%) | `ddas_service.py` |
| Image similarity threshold | 10 (Hamming) | `ddas_service.py` |
| Monitor interval | 5 s | `ddas_service.py` |

---

## Architecture Flow

```
New file detected (Watchdog)
        │
        ▼
Hash Engine → Exact duplicate? → Alert + skip insert
        │
        ▼
Text Engine → Near-duplicate? → Alert + continue
        │
        ▼
Image/Video → Similar media? → Alert + continue
        │
        ▼
Insert into downloads table
```

---

## License

MIT License – SVIIT Minor Project 2026

