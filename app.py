from flask import Flask, render_template, request, jsonify, url_for
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import os
from werkzeug.utils import secure_filename

# Flask app
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static"  # Uploaded files go inside /static

# Load model
MODEL_PATH = "model/Sortify.h5"
model = load_model(MODEL_PATH)
print("✅ Model loaded successfully")

# Image preprocessing
def preprocess(img_path):
    """Preprocess image for model prediction"""
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

# Routes
@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/upload')
def upload_page():
    return render_template('upload.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty file'})
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    # Preprocess + Predict
    img_array = preprocess(filepath)
    preds = model.predict(img_array)[0]

    # Handle both sigmoid (binary) & softmax (multi-class)
    if preds.shape[0] == 1:  
        label = "♻️ Recyclable" if preds[0] > 0.5 else "🚯 Non-Recyclable"
    else:
        label = "♻️ Recyclable" if np.argmax(preds) == 1 else "🚯 Non-Recyclable"

    # Return response
    return jsonify({
        'prediction': label,
        'file_url': url_for('static', filename=filename)
    })

# Run app
if __name__ == "__main__":
    app.run(debug=True)
