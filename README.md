VibeCoding — StudyAI (Flask)

Upload Documents · My Documents · Flashcards · Practice Exams · Peer Learning
VibeCoding Hackathon submission — full-stack Flask app for creating study materials and peer learning

Project Overview

StudyAI is a lightweight web app built with Flask that lets users upload learning materials (PDFs/DOCs/TXT), convert them into study artifacts (flashcards, practice exams), manage their documents, and collaborate with peers in real time. It was created for the VibeCoding Hackathon and focuses on fast feedback loops and an intuitive study flow.

Key flows:

Upload documents and store them per-user

Generate flashcards from uploaded content or from typed topics

Create practice exams (auto-generated or custom)

Peer learning with real-time rooms (chat / collaborative study)

Simple UI (HTML/CSS/JS) and REST + Socket.IO backend

Features

Document upload (PDF, DOCX, TXT, images)

My Documents — list, view, download, delete

Flashcards — generate, create, edit, delete, review mode

Practice Exams — auto-generate MCQs and short-answer questions from content; take timed quizzes; score & review

Peer Learning — real-time rooms using flask-socketio for chat and collaborative sessions

User sessions (simple auth/session-based; can plug in OAuth/JWT)

SQLite by default (easy local setup); optionally PostgreSQL for production

Extensible: plug in NLP/summarization, OpenAI, OCR, or more advanced question generation

Tech Stack

Backend: Python 3.10+, Flask, Flask-SocketIO

Database: SQLite (dev), optional Postgres for production

Frontend: HTML (Jinja2), plain JavaScript (vanilla) — modular static files (/static/js, /static/css)

File storage: local /uploads (dev). S3/Cloud storage recommended for prod.

Optional: python-docx, PyMuPDF (fitz) for PDF parsing, pytesseract for OCR

Dev tools: venv, pip, docker (optional)

Repo Structure (suggested)
studyai/
├─ app.py                    # Flask app (routes + socketio)
├─ models.py                 # DB models (SQLAlchemy)
├─ auth.py                   # auth routes / session helpers
├─ utils/
│  ├─ parser.py              # PDF/DOCX/TXT parsers, OCR helpers
│  ├─ qgen.py                # flashcard & question generation helpers
│  └─ storage.py             # file save/load helpers
├─ templates/
│  ├─ index.html
│  ├─ login.html
│  ├─ upload.html
│  ├─ documents.html
│  ├─ flashcards.html
│  └─ exam.html
├─ static/
│  ├─ css/style.css
│  └─ js/
│     ├─ main.js
│     ├─ flashcards.js
│     └─ socket.js
├─ uploads/                  # uploaded docs (gitignored)
├─ requirements.txt
├─ README.md
└─ .env                      # environment variables (gitignored)

Quick Start — Local (development)

Clone:

git clone https://github.com/<your-username>/studyai-vibecoding.git
cd studyai-vibecoding


Create virtualenv and install:

python -m venv venv
source venv/bin/activate        # mac/linux
# venv\Scripts\activate        # windows
pip install -r requirements.txt


Environment (example .env):

FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=supersecret
DATABASE_URL=sqlite:///data.db
UPLOAD_FOLDER=uploads


Initialize DB:

python -c "from models import db; from app import create_app; app = create_app(); app.app_context().push(); db.create_all()"


Run:

# if using Flask-SocketIO
python app.py
# or:
flask run


Open http://localhost:5000

Example requirements.txt
Flask>=2.1
Flask-SocketIO>=5.3
python-dotenv
Flask-Cors
Flask-SQLAlchemy
Werkzeug
PyMuPDF      # for PDF extraction (optional)
python-docx  # for DOCX parsing (optional)
pytesseract  # optional-ocr
gunicorn     # production
