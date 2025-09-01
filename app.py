from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit, join_room
import os
import sqlite3
from openai import OpenAI

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

DB_PATH = "studyai.db"

# ------------------- DB Helpers -------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        dob TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS flashcards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_id INTEGER NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_id INTEGER NOT NULL,
        question TEXT NOT NULL,
        options TEXT NOT NULL,
        answer TEXT NOT NULL
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT NOT NULL,
        receiver TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

# ------------------- Routes -------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload_document():
    user_id = request.form.get('user_id', 1)
    file = request.files.get('file')
    if not file:
        return jsonify({'success': False, 'message': 'Missing file'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO documents (user_id, filename) VALUES (?,?)", (user_id, filename))
    conn.commit()
    doc_id = cur.lastrowid
    conn.close()

    return jsonify({'success': True, 'message': 'File uploaded', 'document_id': doc_id, 'filename': filename})

# ------------------- Generate Flashcards -------------------
@app.route('/flashcards', methods=['POST'])
def generate_flashcards():
    data = request.get_json()
    doc_ids = data.get('document_ids', [])
    flashcards = []

    conn = get_db()
    cur = conn.cursor()
    for doc_id in doc_ids:
        cur.execute("SELECT filename FROM documents WHERE id=?", (doc_id,))
        doc = cur.fetchone()
        if not doc:
            continue

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], doc['filename'])
        if not os.path.exists(filepath):
            continue

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        prompt = f"""
        Create 5 simple Q&A flashcards from the content below.
        Make answers informative and include relevant context from general knowledge sources.
        Content:
        {content}
        """

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=700
        )

        ai_output = response.choices[0].message.content
        for line in ai_output.split("\n"):
            if "Q:" in line and "A:" in line:
                q, a = line.split("A:", 1)
                question, answer = q.replace("Q:", "").strip(), a.strip()
                flashcards.append({'question': question, 'answer': answer})
                # Save to DB
                cur.execute("INSERT INTO flashcards (doc_id, question, answer) VALUES (?,?,?)", (doc_id, question, answer))

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'flashcards': flashcards})

# ------------------- Generate Exams -------------------
@app.route('/exams', methods=['POST'])
def generate_exams():
    data = request.get_json()
    doc_ids = data.get('document_ids', [])
    exams = []

    conn = get_db()
    cur = conn.cursor()
    for doc_id in doc_ids:
        cur.execute("SELECT filename FROM documents WHERE id=?", (doc_id,))
        doc = cur.fetchone()
        if not doc:
            continue

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], doc['filename'])
        if not os.path.exists(filepath):
            continue

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        prompt = f"""
        Create 3 multiple-choice questions (4 options each) from this content.
        Make the questions educational and include relevant context from general knowledge sources.
        Specify the correct answer for each question.
        Content:
        {content}
        """

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=700
        )

        ai_output = response.choices[0].message.content
        for line in ai_output.split("\n"):
            if "Q:" in line:
                parts = line.split("Options:")
                question = parts[0].replace("Q:", "").strip()
                options = parts[1].split(",") if len(parts) > 1 else ['A', 'B', 'C', 'D']
                exams.append({'question': question, 'options': [opt.strip() for opt in options], 'answer': options[0].strip()})
                # Save to DB
                cur.execute("INSERT INTO exams (doc_id, question, options, answer) VALUES (?,?,?,?)",
                            (doc_id, question, ",".join([opt.strip() for opt in options]), options[0].strip()))

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'exams': exams})

# ------------------- Peer Learning -------------------
@app.route('/peers', methods=['POST'])
def peer_learning():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT username FROM users LIMIT 5")
    peers = [row['username'] for row in cur.fetchall()]
    conn.close()
    return jsonify({'success': True, 'peers': peers})

@app.route('/messages/<peer>', methods=['GET'])
def get_messages(peer):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT sender, message, created_at FROM messages WHERE receiver=? OR sender=? ORDER BY created_at ASC", (peer, peer))
    msgs = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify({'success': True, 'messages': msgs})

# ------------------- Socket.IO -------------------
@socketio.on('join')
def on_join(data):
    username = data['username']
    peer = data['peer']
    room = "_".join(sorted([username, peer]))
    join_room(room)
    emit('status', {'msg': f"{username} joined {room}"}, room=room)

@socketio.on('send_message')
def handle_message(data):
    sender = data['sender']
    receiver = data['receiver']
    message = data['message']
    room = "_".join(sorted([sender, receiver]))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO messages (sender, receiver, message) VALUES (?,?,?)", (sender, receiver, message))
    conn.commit()
    conn.close()

    emit('receive_message', {'sender': sender, 'message': message}, room=room)

# ------------------- Main -------------------
if __name__ == '__main__':
    create_tables()
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
