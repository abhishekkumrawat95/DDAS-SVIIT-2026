\# DDAS – Data Download Duplication Alert System



\*\*SVIIT Minor Project 2026\*\* | Week 6 Deliverables



\## Project Overview

Data Download Duplication Alert System for single PC with multiple users.

Prevents redundant downloads by detecting duplicates via hashing.



\## Architecture

DDAS/

├── ddas\_service.py (Watchdog file monitoring)

├── ddas\_tray.py (pystray notifications)

├── ddas\_dashboard.py (Tkinter UI)

├── detection/

│ ├── hash\_engine.py (SHA-256 exact duplicates)

│ ├── text\_similarity.py (TF-IDF similar docs)

│ └── image\_video\_detect.py (pHash for media)

├── chatbot/

│ └── chatbot\_engine.py (File availability queries)

└── db/

└── db\_helper.py (SQLite database)



\## Tech Stack

\- Python 3.11+

\- Watchdog, pystray, plyer, Pillow, scikit-learn

\- Tkinter (UI), SQLite (DB)



\## Team

\- \*\*Abhishek Kumrawat\*\* (Leader, Project Management)

\- \*\*Member 2\*\* (Database, Backend)

\- \*\*Member 3\*\* (Notifications, Chatbot)

\- \*\*Member 4\*\* (Dashboard UI)



\## Setup Instructions

```bash

git clone https://github.com/abhishekkumrawat/DDAS-SVIIT-2026.git

cd DDAS-SVIIT-2026

python -m venv venv

venv\\Scripts\\activate

pip install -r requirements.txt

python db/db\_helper.py  # Initialize database





