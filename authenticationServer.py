from flask import Flask, request as flaskReq, jsonify
import sqlite3
import secrets
import hashlib
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Configuration
DATABASE = 'auth.db'
ACCESS_TOKEN_EXPIRY_MINUTES = 10  # Can be changed as needed

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with required tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Refresh tokens table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Access tokens table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS access_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def generate_token():
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/signup', methods=['POST'])
def signup():
    """
    Sign up a new user
    Input: {"username": "string", "password_hash": "string"}
    Output: {"refresh_token": "string", "user_id": int}
    """
    try:
        data = flaskReq.get_json()
        username = data.get('username')
        password_hash = data.get('password_hash')
        
        if not username or not password_hash:
            return jsonify({'error': 'username and password_hash are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            return jsonify({'error': 'User already exists'}), 409
        
        # Create new user
        cursor.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, password_hash)
        )
        user_id = cursor.lastrowid
        
        # Generate refresh token
        refresh_token = generate_token()
        cursor.execute(
            'INSERT INTO refresh_tokens (user_id, token) VALUES (?, ?)',
            (user_id, refresh_token)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'refresh_token': refresh_token,
            'user_id': user_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/authenticate', methods=['POST'])
def authenticate():
    """
    Authenticate user credentials
    Input: {"username": "string", "password_hash": "string"}
    Output: {"refresh_token": "string", "user_id": int}
    """
    try:
        data = flaskReq.get_json()
        username = data.get('username')
        password_hash = data.get('password_hash')
        
        if not username or not password_hash:
            return jsonify({'error': 'Username and password_hash are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Authenticate user
        cursor.execute(
            'SELECT id FROM users WHERE username = ? AND password_hash = ?',
            (username, password_hash)
        )
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        user_id = user[0]
        
        # Get existing refresh token or create new one
        cursor.execute(
            'SELECT token FROM refresh_tokens WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
            (user_id,)
        )
        existing_token = cursor.fetchone()
        
        if existing_token:
            refresh_token = existing_token[0]
        else:
            refresh_token = generate_token()
            cursor.execute(
                'INSERT INTO refresh_tokens (user_id, token) VALUES (?, ?)',
                (user_id, refresh_token)
            )
            conn.commit()
        
        conn.close()
        
        return jsonify({
            'refresh_token': refresh_token,
            'user_id': user_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate-access-token', methods=['POST'])
def generate_access_token():
    """
    Generate access token using refresh token
    Input: {"user_id": int, "refresh_token": "string"}
    Output: {"access_token": "string", "expires_at": "string"}
    """
    try:
        data = flaskReq.get_json()
        user_id = data.get('user_id')
        refresh_token = data.get('refresh_token')
        
        if not user_id or not refresh_token:
            return jsonify({'error': 'user_id and refresh_token are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Validate refresh token
        cursor.execute(
            'SELECT id FROM refresh_tokens WHERE user_id = ? AND token = ?',
            (user_id, refresh_token)
        )
        if not cursor.fetchone():
            return jsonify({'error': 'Invalid refresh token'}), 401
        
        # Generate access token
        access_token = generate_token()
        expires_at = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES)
        
        # Clean up expired access tokens for this user
        cursor.execute(
            'DELETE FROM access_tokens WHERE user_id = ? AND expires_at < ?',
            (user_id, datetime.now())
        )
        
        # Store new access token
        cursor.execute(
            'INSERT INTO access_tokens (user_id, token, expires_at) VALUES (?, ?, ?)',
            (user_id, access_token, expires_at)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'access_token': access_token,
            'expires_at': expires_at.isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/authenticate-token', methods=['POST'])
def authenticate_token():
    """
    Authenticate access token
    Input: {"user_id": int, "access_token": "string"}
    Output: {"valid": bool, "expires_at": "string"}
    """
    try:
        data = flaskReq.get_json()
        user_id = data.get('user_id')
        access_token = data.get('access_token')
        
        if not user_id or not access_token:
            return jsonify({'error': 'user_id and access_token are required'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if access token exists and is not expired
        cursor.execute(
            'SELECT expires_at FROM access_tokens WHERE user_id = ? AND token = ? AND expires_at > ?',
            (user_id, access_token, datetime.now())
        )
        token_data = cursor.fetchone()
        
        conn.close()
        
        if token_data:
            return jsonify({
                'valid': True,
                'expires_at': token_data[0]
            }), 200
        else:
            return jsonify({
                'valid': False,
                'message': 'Token is invalid or expired'
            }), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)