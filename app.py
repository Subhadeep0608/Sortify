from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import os
import uuid


# Flask setup

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER", "static/uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


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

@app.route("/upload")
def upload_page():
    return render_template("upload.html")

@app.route("/health")
def health():
    return jsonify({
        "model_loaded": model_loaded,
        "model_error": model_error,
        "blockchain_connected": False,  # No real contract
        "contract_loaded": False
    })

@app.route("/predict", methods=["POST"])
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

        user_wallet = request.form.get("wallet", "DEMO_WALLET")
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
