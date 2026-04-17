# DDAS – Data Download Duplication Alert System

**SVIIT Minor Project 2026** · Group G-15 · BTCS607N

---

## Project Overview

DDAS detects duplicate file downloads on a shared PC with multiple users and
notifies them in real time. It combines exact hash-based matching, text
similarity (TF-IDF), and perceptual image/video hashing with an integrated
chatbot that queries both the local database and the web.

---

## Architecture

```
DDAS-SVIIT-2026/
├── main.py                     # Application entry point (service + tray + dashboard)
├── chatbot_cli.py              # Chatbot command-line interface
├── api_server.py               # Flask REST API server
├── config.py                   # Central configuration (reads from .env)
├── ddas_service.py             # Watchdog file-monitoring service
├── ddas_tray.py                # System-tray notifications (pystray)
├── ddas_dashboard.py           # Tkinter dashboard GUI
├── detection/
│   ├── hash_engine.py          # SHA-256 exact duplicate detection
│   ├── text_similarity.py      # TF-IDF cosine similarity for documents
│   └── image_video_detect.py   # pHash for images & video fingerprinting
├── chatbot/
│   └── chatbot_engine.py       # Chatbot: local DB + optional DuckDuckGo search
├── db/
│   ├── db_helper.py            # SQLite CRUD helpers
│   └── init_db.py              # Database initialisation & schema creation
├── data/                       # Auto-created at runtime (DB, logs)
├── requirements.txt
├── .env.example                # Environment variable template
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| File Monitoring | Watchdog |
| Exact Duplicate | SHA-256 (hashlib) |
| Text Similarity | scikit-learn TF-IDF |
| Image/Video | Pillow + ImageHash (pHash), OpenCV |
| Database | SQLite (built-in) |
| GUI | Tkinter |
| System Tray | pystray + plyer |
| REST API | Flask |
| Chatbot | Local DB search + DuckDuckGo Lite (optional) |

---

## Team

- **Abhishek Kumrawat** (Leader, Project Management)
- **Member 2** (Database, Backend)
- **Member 3** (Notifications, Chatbot)
- **Member 4** (Dashboard UI)

---

## Setup Instructions

```bash
# 1. Clone the repository
git clone https://github.com/abhishekkumrawat95/DDAS-SVIIT-2026.git
cd DDAS-SVIIT-2026

# 2. Create & activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment (optional)
cp .env.example .env
# Edit .env to set DDAS_MONITOR_FOLDERS, email settings, etc.

# 5. Initialise the database
python db/init_db.py

# 6. Run the full application (monitor + tray + dashboard)
python main.py

# Or run individual components:
python main.py --service-only     # File monitor only
python main.py --dashboard-only   # Dashboard only
python api_server.py              # REST API only
python chatbot_cli.py             # Chatbot CLI only
```

---

## REST API Reference

Base URL: `http://127.0.0.1:5000`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Service health check |
| GET | `/api/downloads` | List all tracked downloads |
| GET | `/api/alerts?user=<name>` | List alerts (filter by user) |
| PATCH | `/api/alerts/<id>` | Update alert status |
| POST | `/api/chatbot` | Query the chatbot |
| GET | `/api/stats` | Summary statistics |

### Chatbot API Example

```bash
curl -X POST http://127.0.0.1:5000/api/chatbot \
  -H "Content-Type: application/json" \
  -d '{"query": "do we have any PDF reports?", "username": "john"}'
```

Response:
```json
{
  "query": "do we have any PDF reports?",
  "local_results": [],
  "online_results": [],
  "summary": "Found 3 file(s) in the local database matching 'PDF'..."
}
```

---

## Chatbot Feature

The chatbot answers natural-language questions about files tracked in DDAS.

**Capabilities:**
- Search local database by filename or extracted text content
- Optionally fetch results from DuckDuckGo (set `ONLINE_SEARCH_ENABLED=true`)
- Persists chat history in the database
- Accessible via CLI (`chatbot_cli.py`), REST API, and the Tkinter dashboard

```bash
# Interactive mode
python chatbot_cli.py --user john

# Single query
python chatbot_cli.py --query "show all excel files" --user john
```

---

## Database Schema

| Table | Description |
|-------|-------------|
| `downloads` | All tracked file downloads with hash, path, user, timestamp |
| `alerts` | Duplicate-detection alerts with severity and resolution status |
| `users` | System users with roles |
| `monitored_folders` | Folders being watched |
| `chat_history` | Chatbot query/response log |

---

## Project Progress

| Week | Deliverable | Status |
|------|-------------|--------|
| 3 | Object Diagram & Class Diagram | Done |
| 4 | Activity Diagram | Done |
| 5 | Sequence Diagrams (3 use cases) | Done |
| 6 | Detailed Class Diagram & Package Diagram | Done |
| 7 | Component & Deployment Diagrams | Done |
| 8+ | Core Implementation | Done |
