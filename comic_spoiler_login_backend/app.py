import uuid
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from m_spoiler_detector import run_pipeline
import os
import sqlite3
from werkzeug.utils import secure_filename
from argon2 import PasswordHasher

import re

app = Flask(__name__)
CORS(app)

# password hasher argon2
ph = PasswordHasher()

app.secret_key = 'your-very-secret-key'  # Replace with something strong in production

# Temporary upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# === SQLite setup ===
DB_PATH = os.path.join(os.path.dirname(__file__), 'users.db')

def create_users_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

create_users_table()

# password validation

def is_valid_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True

# === Routes ===

@app.route('/')
def home():
    return "Backend is working!"

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'Username, email and password required'}), 400

    if not is_valid_password(password):
        return jsonify({
            'error': 'Password must be at least 8 chars, include uppercase, lowercase, number, and special char.'
        }), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        hashed_password = ph.hash(password)
        cursor.execute(
            'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
            (username, email, hashed_password)
        )
        conn.commit()
        return jsonify({'message': 'Signup successful'}), 200
    except sqlite3.IntegrityError:
        return jsonify({'error': 'User already exists'}), 409
    finally:
        conn.close()


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT email, password FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    email, stored_hash = user

    try:
        ph.verify(stored_hash, password)
    except Exception:
        return jsonify({'error': 'Invalid credentials'}), 401

    session['user'] = username
    return jsonify({
        'message': 'Login successful',
        'username': username,
        'email': email
    }), 200




@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/analyze', methods=['POST'])
def analyze_image():
    if not session.get('user'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized: please login first'}), 401

    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    image_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(image_path)

    try:
        result = run_pipeline(image_path)
        return jsonify({
            "extracted_text": result.get("text", ""),
            "caption": result.get("caption", ""),
            "genre": result.get("genre", ""),
            "character_count": result.get("character_count", 0),
            "spoiler_result": result.get("result", "Unknown")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Optional: Clean up uploaded file
        os.remove(image_path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
