import traceback
import uuid
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from m_spoiler_detector import run_pipeline
import os
# import sqlite3
from psycopg2 import IntegrityError
from werkzeug.utils import secure_filename
from argon2 import PasswordHasher
from dotenv import load_dotenv
import re
import psycopg2

import logging

logging.basicConfig(level=logging.INFO)

from pathlib import Path

dotenv_path = Path(__file__).parent / ".env"
print("Loading env from:", dotenv_path)
load_dotenv(dotenv_path, override=True)

print("DB_HOST:", os.getenv("DB_HOST"))

app = Flask(__name__)
CORS(app)

# password hasher argon2
ph = PasswordHasher()

print("Current working dir:", os.getcwd())
print("Files in cwd:", os.listdir())

load_dotenv()
print("DB_HOST:", os.getenv("DB_HOST"))

# app.secret_key = 'the-hardest-secret-key-to-crack'  # Replace with something strong in production
app.secret_key = os.getenv('SECRET_KEY')  # Replace with something strong in production

# Temporary upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Get config from .env
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

def get_db_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def create_users_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    cursor.close()
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

    logging.info(f"Signup attempt: {email}, Username: {username}")

    if not username or not email or not password:
        return jsonify({'error': 'Username, email and password required'}), 400

    if not is_valid_password(password):
        logging.info(f"Rejected weak password for: {email}")
        return jsonify({
            'error': 'Password must be at least 8 chars, include uppercase, lowercase, number, and special char.'
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        hashed_password = ph.hash(password)
        cursor.execute(
            'INSERT INTO users (username, email, password) VALUES (%s, %s, %s)',
            (username, email, hashed_password)
        )
        conn.commit()
        return jsonify({'message': 'Signup successful'}), 200
    except IntegrityError:
        logging.info(f"User already exists.")
        return jsonify({'error': 'User already exists'}), 409
    finally:
        logging.info(f"New user created: {email}")
        conn.close()
    


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        logging.info(f"Login failed: missing username or password")
        return jsonify({'error': 'Username and password required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT email, password FROM users WHERE username = %s', (username,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        logging.info(f"Login failed for username: {username} — user not found")
        return jsonify({'error': 'Invalid credentials'}), 401

    email, stored_hash = user

    try:
        ph.verify(stored_hash, password)
    except Exception:
        logging.info(f"Login failed for username: {username} — invalid password")
        return jsonify({'error': 'Invalid credentials'}), 401

    session['user'] = username
    logging.info(f"Login success for username: {username}")
    return jsonify({
        'message': 'Login successful',
        'username': username,
        'email': email
    }), 200




@app.route('/logout', methods=['POST'])
def logout():

    session.pop('user', None)
    logging.info(f"Logout: User has logged out.")
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/analyze', methods=['POST'])
def analyze_image():

    if not session.get('user'):
        logging.info("Analyze attempt failed: Unauthorized")
        return jsonify({'error': 'Unauthorized'}), 401
    
    if 'user' not in session:
        logging.info(f"Need to login first.")
        return jsonify({'error': 'Unauthorized: please login first'}), 401

    if 'image' not in request.files:
        logging.info(f"Analyze failed: No image provided")
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    if file.filename == '':
        logging.info(f"Analyze failed, empty file.")
        return jsonify({'error': 'Empty filename'}), 400

    filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    image_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(image_path)

    logging.info(f"Analyze started.")
    try:
        result = run_pipeline(image_path)
        logging.info(f"Analyze success for user.")
        return jsonify({
            "extracted_text": result.get("text", ""),
            "caption": result.get("caption", ""),
            "genre": result.get("genre", ""),
            "character_count": result.get("character_count", 0),
            "spoiler_result": result.get("result", "Unknown")
        })
    except Exception as e:
        logging.error(f"Analyze failed for user.")
        logging.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    finally:
        # Optional: Clean up uploaded file
        os.remove(image_path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
