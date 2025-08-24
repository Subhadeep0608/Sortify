from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import os
import uuid
import sqlite3
import re
from functools import wraps

# Flask setup
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER", "static/uploads")
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

# Database setup
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Create users table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  wallet_address TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Check if wallet_address column exists, if not add it
    try:
        c.execute("SELECT wallet_address FROM users LIMIT 1")
    except sqlite3.OperationalError:
        print("Adding wallet_address column to users table...")
        c.execute("ALTER TABLE users ADD COLUMN wallet_address TEXT")
    
    conn.commit()
    conn.close()

init_db()

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# Load ML Model
MODEL_PATH = os.environ.get("MODEL_PATH", "model/Sortify.h5")
model_loaded = False
model_error = None

try:
    model = load_model(MODEL_PATH, compile=False)
    model_loaded = True
    print("✅ Model loaded successfully")
except Exception as e:
    model_error = str(e)
    model = None
    print(f"❌ Failed to load model: {model_error}")

def preprocess(img_path):
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

def interpret_prediction(preds: np.ndarray) -> bool:
    preds = np.array(preds)
    if preds.ndim == 1:
        if preds.shape[0] == 1:
            return preds[0] > 0.5
        return int(np.argmax(preds)) == 1
    if preds.ndim == 2:
        if preds.shape[1] == 1:
            return preds[0,0] > 0.5
        return int(np.argmax(preds[0])) == 1
    return False

# Simulated Blockchain Reward
def send_reward_to_user(user_address: str, points: int = 10):
    """
    Simulate sending reward. Returns a dummy tx hash.
    """
    if not user_address:
        return "Error: Invalid wallet"
    return f"SIMULATED_TX_HASH_{uuid.uuid4().hex[:8]}"

# Dummy NGOs
NGOS = [
    {"id": 1, "name": "Green Earth Foundation", "contact": "green@ngo.org"},
    {"id": 2, "name": "Recycle India", "contact": "recycle@ngo.org"},
    {"id": 3, "name": "EcoSavers", "contact": "eco@ngo.org"},
]

# Routes
@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/login.html")
def login_page():
    return render_template("login.html")

@app.route("/signup.html") 
def signup_page():
    return render_template("signup.html")

@app.route("/login", methods=["POST"])
def handle_login():
    """Handle login form submission"""
    try:
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        
        if not email or not password:
            flash("Email and password are required", "error")
            return redirect(url_for('login_page'))
        
        # Check user credentials
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT id, name, password FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['user_email'] = email
            flash("Login successful!", "success")
            return redirect(url_for('upload_page'))
        else:
            flash("Invalid email or password", "error")
            return redirect(url_for('login_page'))
        
    except Exception as e:
        flash(f"Login failed: {str(e)}", "error")
        return redirect(url_for('login_page'))

@app.route("/signup", methods=["POST"])
def handle_signup():
    """Handle signup form submission"""
    try:
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip() 
        password = request.form.get("password", "").strip()
        wallet_address = request.form.get("wallet", "").strip()
        
        if not all([name, email, password]):
            flash("Name, email and password are required", "error")
            return redirect(url_for('signup_page'))
        
        # Validate email format
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash("Invalid email format", "error")
            return redirect(url_for('signup_page'))
        
        # Check if user already exists
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE email = ?", (email,))
        if c.fetchone():
            conn.close()
            flash("Email already registered", "error")
            return redirect(url_for('signup_page'))
            
        # Create new user
        hashed_password = generate_password_hash(password)
        c.execute("INSERT INTO users (name, email, password, wallet_address) VALUES (?, ?, ?, ?)",
                 (name, email, hashed_password, wallet_address))
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        
        # Log user in
        session['user_id'] = user_id
        session['user_name'] = name
        session['user_email'] = email
        
        flash("Account created successfully!", "success")
        return redirect(url_for('upload_page'))
        
    except sqlite3.OperationalError as e:
        if "no such column: wallet_address" in str(e):
            # Database schema issue - try to fix it
            try:
                conn = sqlite3.connect('users.db')
                c = conn.cursor()
                c.execute("ALTER TABLE users ADD COLUMN wallet_address TEXT")
                conn.commit()
                conn.close()
                flash("Database updated. Please try signing up again.", "info")
                return redirect(url_for('signup_page'))
            except:
                flash("Database error. Please contact administrator.", "error")
                return redirect(url_for('signup_page'))
        else:
            flash(f"Signup failed: {str(e)}", "error")
            return redirect(url_for('signup_page'))
    except Exception as e:
        flash(f"Signup failed: {str(e)}", "error")
        return redirect(url_for('signup_page'))

@app.route("/logout")
def logout():
    """Handle user logout"""
    session.clear()
    flash("You have been logged out", "info")
    return redirect(url_for('landing'))

@app.route("/upload")
@login_required
def upload_page():
    return render_template("upload.html")

@app.route("/dashboard")
@login_required
def dashboard():
    """User dashboard page"""
    return render_template("dashboard.html", user_name=session.get('user_name'))

@app.route("/health")
def health():
    return jsonify({
        "model_loaded": model_loaded,
        "model_error": model_error,
        "blockchain_connected": False,
        "contract_loaded": False
    })

@app.route("/predict", methods=["POST"])
@login_required
def predict():
    if not model_loaded:
        return jsonify({"error": f"Model not loaded: {model_error}"}), 500

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty file"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"}), 400

    # Save file
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file.save(file_path)

    try:
        img_array = preprocess(file_path)
        preds = model.predict(img_array, verbose=0)
        recyclable = interpret_prediction(preds)
        label = "recyclable" if recyclable else "non-recyclable"

        # Get user's wallet address from database
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT wallet_address FROM users WHERE id = ?", (session['user_id'],))
        wallet_result = c.fetchone()
        user_wallet = wallet_result[0] if wallet_result and wallet_result[0] else "DEMO_WALLET"
        conn.close()
        
        reward_tx = send_reward_to_user(user_wallet) if recyclable else None

        return jsonify({
            "prediction": label,
            "file_path": "/" + file_path.replace("\\", "/"),
            "reward_tx": reward_tx,
            "ngos": NGOS if recyclable else []
        })
    except Exception as e:
        return jsonify({"error": f"Inference failed: {str(e)}"}), 500

@app.route("/static/uploads/<path:filename>")
def serve_uploads(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# Demo Wallet Balance Route
@app.route("/wallet/<wallet>")
def wallet_balance(wallet):
    return jsonify({"balance": 123})  # Simulated balance

# Run App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)