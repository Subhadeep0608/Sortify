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
import math
from functools import wraps
from datetime import datetime
from geopy.distance import geodesic  # Install with: pip install geopy

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
                  latitude REAL,
                  longitude REAL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Create user_activity table for dashboard
    c.execute('''CREATE TABLE IF NOT EXISTS user_activity
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  activity_type TEXT NOT NULL,
                  activity_details TEXT,
                  points_earned INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Create NGOs table with location data
    c.execute('''CREATE TABLE IF NOT EXISTS ngos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  description TEXT,
                  category TEXT,
                  email TEXT,
                  phone TEXT,
                  website TEXT,
                  address TEXT,
                  latitude REAL,
                  longitude REAL,
                  city TEXT,
                  accepts_recyclables BOOLEAN DEFAULT TRUE,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Check if wallet_address column exists, if not add it
    try:
        c.execute("SELECT wallet_address FROM users LIMIT 1")
    except sqlite3.OperationalError:
        print("Adding wallet_address column to users table...")
        c.execute("ALTER TABLE users ADD COLUMN wallet_address TEXT")
    
    # Check if latitude/longitude columns exist, if not add them
    try:
        c.execute("SELECT latitude FROM users LIMIT 1")
    except sqlite3.OperationalError:
        print("Adding latitude/longitude columns to users table...")
        c.execute("ALTER TABLE users ADD COLUMN latitude REAL")
        c.execute("ALTER TABLE users ADD COLUMN longitude REAL")
    
    # Insert sample NGOs if table is empty
    c.execute("SELECT COUNT(*) FROM ngos")
    if c.fetchone()[0] == 0:
        sample_ngos = [
            ('Green Earth Foundation', 'Environmental conservation and waste management', 'Environment', 
             'contact@greenearth.org', '+1234567890', 'https://greenearth.org', 
             '123 Eco Street, Green City', 12.9716, 77.5946, 'Bangalore', True),
            ('Recycle India', 'Nationwide recycling initiative', 'Recycling', 
             'info@recycleindia.org', '+1987654321', 'https://recycleindia.org', 
             '456 Green Avenue, Eco Town', 28.6139, 77.2090, 'Delhi', True),
            ('EcoSavers', 'Community-based environmental organization', 'Community', 
             'hello@ecosavers.org', '+1122334455', 'https://ecosavers.org', 
             '789 Nature Road, Sustainable City', 19.0760, 72.8777, 'Mumbai', True),
            ('Waste Warriors', 'Fighting waste through education and action', 'Education', 
             'contact@wastewarriors.org', '+1567890123', 'https://wastewarriors.org', 
             '321 Clean Lane, Green Valley', 13.0827, 80.2707, 'Chennai', True),
            ('Planet Protectors', 'Youth-led environmental initiative', 'Youth', 
             'join@planetprotectors.org', '+1456789012', 'https://planetprotectors.org', 
             '654 Earth Boulevard, Eco District', 17.3850, 78.4867, 'Hyderabad', True)
        ]
        
        c.executemany('''INSERT INTO ngos (name, description, category, email, phone, website, 
                      address, latitude, longitude, city, accepts_recyclables) 
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', sample_ngos)
    
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
            return redirect(url_for('landing'))
        return f(*args, **kwargs)
    return decorated_function

# Log user activity
def log_activity(user_id, activity_type, details=None, points=0):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO user_activity (user_id, activity_type, activity_details, points_earned) VALUES (?, ?, ?, ?)",
                 (user_id, activity_type, details, points))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging activity: {e}")

# Geolocation functions
def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in kilometers"""
    try:
        return geodesic((lat1, lon1), (lat2, lon2)).km
    except:
        # Fallback calculation if geopy is not available
        R = 6371  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * \
            math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

def get_nearby_ngos(user_lat, user_lon, max_distance_km=50, limit=10):
    """Find NGOs near the user's location"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # For SQLite, we need to calculate distance for each row
    c.execute('SELECT * FROM ngos WHERE accepts_recyclables = TRUE')
    all_ngos = c.fetchall()
    
    nearby_ngos = []
    for ngo in all_ngos:
        ngo_lat, ngo_lon = ngo[8], ngo[9]  # latitude and longitude columns
        if ngo_lat and ngo_lon:
            distance = calculate_distance(user_lat, user_lon, ngo_lat, ngo_lon)
            if distance <= max_distance_km:
                ngo_data = {
                    'id': ngo[0],
                    'name': ngo[1],
                    'description': ngo[2],
                    'category': ngo[3],
                    'email': ngo[4],
                    'phone': ngo[5],
                    'website': ngo[6],
                    'address': ngo[7],
                    'latitude': ngo[8],
                    'longitude': ngo[9],
                    'city': ngo[10],
                    'accepts_recyclables': bool(ngo[11]),
                    'distance': round(distance, 1)
                }
                nearby_ngos.append(ngo_data)
    
    # Sort by distance and limit results
    nearby_ngos.sort(key=lambda x: x['distance'])
    conn.close()
    return nearby_ngos[:limit]

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

# Routes
@app.route("/")
def landing():
    # If user is logged in, show the main landing page
    if 'user_id' in session:
        return render_template("landing.html", 
                             user_name=session.get('user_name'),
                             logged_in=True)
    # If not logged in, show the auth-focused landing page
    return render_template("landing.html", logged_in=False)

@app.route("/login.html")
def login_page():
    # Redirect to home if already logged in
    if 'user_id' in session:
        return redirect(url_for('landing'))
    return render_template("login.html")

@app.route("/signup.html") 
def signup_page():
    # Redirect to home if already logged in
    if 'user_id' in session:
        return redirect(url_for('landing'))
    return render_template("signup.html")

@app.route("/login", methods=["POST"])
def handle_login():
    """Handle login form submission"""
    # Redirect to home if already logged in
    if 'user_id' in session:
        return redirect(url_for('landing'))
    
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
            
            # Log login activity
            log_activity(user[0], "login", "User logged in successfully")
            
            flash("Login successful!", "success")
            return redirect(url_for('landing'))
        else:
            flash("Invalid email or password", "error")
            return redirect(url_for('login_page'))
        
    except Exception as e:
        flash(f"Login failed: {str(e)}", "error")
        return redirect(url_for('login_page'))

@app.route("/signup", methods=["POST"])
def handle_signup():
    """Handle signup form submission"""
    # Redirect to home if already logged in
    if 'user_id' in session:
        return redirect(url_for('landing'))
    
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
        
        # Log signup activity
        log_activity(user_id, "signup", "New user account created")
        
        flash("Account created successfully!", "success")
        return redirect(url_for('landing'))
        
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
    if 'user_id' in session:
        # Log logout activity
        log_activity(session['user_id'], "logout", "User logged out")
    
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
    # Get user's activity history
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''SELECT activity_type, activity_details, points_earned, created_at 
                 FROM user_activity 
                 WHERE user_id = ? 
                 ORDER BY created_at DESC 
                 LIMIT 20''', (session['user_id'],))
    activities = c.fetchall()
    
    # Get total points
    c.execute('''SELECT SUM(points_earned) FROM user_activity WHERE user_id = ?''', 
              (session['user_id'],))
    total_points = c.fetchone()[0] or 0
    
    # Get user's wallet address
    c.execute('''SELECT wallet_address FROM users WHERE id = ?''', (session['user_id'],))
    wallet_result = c.fetchone()
    wallet_address = wallet_result[0] if wallet_result else "Not set"
    
    conn.close()
    
    return render_template("dashboard.html", 
                         user_name=session.get('user_name'),
                         activities=activities,
                         total_points=total_points,
                         wallet_address=wallet_address)

@app.route("/features")
def features_page():
    return render_template("feature.html")

@app.route("/ngos")
@login_required
def ngos_page():
    """NGO listing page"""
    return render_template("ngos.html")

@app.route("/api/ngos/nearby", methods=["GET"])
@login_required
def nearby_ngos():
    """Get NGOs near the user's location"""
    try:
        # Get user's location from request
        user_lat = request.args.get('lat', type=float)
        user_lon = request.args.get('lon', type=float)
        
        # If no coordinates provided, use a default location
        if user_lat is None or user_lon is None:
            # Try to get from user's profile if stored
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute("SELECT latitude, longitude FROM users WHERE id = ?", (session['user_id'],))
            location = c.fetchone()
            conn.close()
            
            if location and location[0] and location[1]:
                user_lat, user_lon = location[0], location[1]
            else:
                # Default to Bangalore coordinates
                user_lat, user_lon = 12.9716, 77.5946
        
        max_distance = request.args.get('max_distance', 50, type=float)  # km
        ngos = get_nearby_ngos(user_lat, user_lon, max_distance)
        
        return jsonify({
            'success': True,
            'user_location': {'lat': user_lat, 'lon': user_lon},
            'ngos': ngos,
            'count': len(ngos)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/api/ngos/contact", methods=["POST"])
@login_required
def contact_ngo():
    """Handle NGO contact form submission"""
    try:
        data = request.get_json()
        ngo_id = data.get('ngo_id')
        message = data.get('message', '')
        
        # Get user info
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT name, email FROM users WHERE id = ?", (session['user_id'],))
        user = c.fetchone()
        
        # Get NGO info
        c.execute("SELECT name, email FROM ngos WHERE id = ?", (ngo_id,))
        ngo = c.fetchone()
        
        if not user or not ngo:
            return jsonify({'success': False, 'error': 'User or NGO not found'}), 404
        
        user_name, user_email = user
        ngo_name, ngo_email = ngo
        
        # Here you would typically:
        # 1. Save the contact request to the database
        # 2. Send an email to the NGO
        # 3. Send a confirmation email to the user
        
        # For now, we'll just log it
        print(f"Contact request from {user_name} ({user_email}) to {ngo_name} ({ngo_email}): {message}")
        
        # Log the activity
        log_activity(session['user_id'], 'ngo_contact', 
                    f"Contacted {ngo_name} about recycling", 0)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Contact request sent successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
        
        reward_tx = None
        points_earned = 0
        
        if recyclable:
            reward_tx = send_reward_to_user(user_wallet)
            points_earned = 10
            # Log recycling activity with points
            log_activity(session['user_id'], "recycling", 
                        f"Recycled item: {filename}", points_earned)
        else:
            # Log non-recyclable activity
            log_activity(session['user_id'], "scan", 
                        f"Scanned non-recyclable item: {filename}")
        
        # Get NGOs from database instead of hardcoded list
        c.execute("SELECT id, name, email FROM ngos WHERE accepts_recyclables = TRUE LIMIT 5")
        db_ngos = [{"id": row[0], "name": row[1], "contact": row[2]} for row in c.fetchall()]
        
        conn.close()

        return jsonify({
            "prediction": label,
            "file_path": "/" + file_path.replace("\\", "/"),
            "reward_tx": reward_tx,
            "points_earned": points_earned,
            "ngos": db_ngos if recyclable else []
        })
    except Exception as e:
        return jsonify({"error": f"Inference failed: {str(e)}"}), 500

@app.route("/static/uploads/<path:filename>")
def serve_uploads(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# Demo Wallet Balance Route
@app.route("/wallet/<wallet>")
@login_required
def wallet_balance(wallet):
    # Get user's total points from activity log
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''SELECT SUM(points_earned) FROM user_activity WHERE user_id = ?''', 
              (session['user_id'],))
    total_points = c.fetchone()[0] or 0
    conn.close()
    
    return jsonify({"balance": total_points})

# Run App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)