import uuid
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from m_spoiler_detector import run_pipeline
import os
import sqlite3
from werkzeug.utils import secure_filename
from argon2 import PasswordHasher

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
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

create_users_table()

# === Routes ===

@app.route('/')
def home():
    return "Backend is working!"

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # hashed password
        hashed_password = ph.hash(password)
        cursor.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, hashed_password))
        conn.commit()
        return jsonify({'message': 'Signup successful'}), 200
    except sqlite3.IntegrityError:
        return jsonify({'error': 'User already exists'}), 409
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT password FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    stored_hash = user[0]

    # if user:
    #     session['user'] = email  # Mark session as logged in
    #     return jsonify({'message': 'Login successful'}), 200
    # else:
    #     return jsonify({'error': 'Invalid credentials'}), 401

    try:
        ph.verify(stored_hash, password)
    except Exception:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    session['user'] = email
    return jsonify({'message': 'Login successful'}), 200



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
