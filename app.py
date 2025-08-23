from flask import Flask, render_template, request, jsonify
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
MODEL_PATH = "model/Sortify.h5"

# Load model
model = load_model(MODEL_PATH)
print("✅ Model loaded successfully")

def preprocess(img_path):
    """Preprocess image for model prediction"""
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

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
    filepath = os.path.join("static", filename)
    file.save(filepath)

    # Preprocess and predict
    img_array = preprocess(filepath)
    preds = model.predict(img_array)[0]

    # Handle both sigmoid (1 output) and softmax (2 outputs) cases
    if preds.shape[0] == 1:  
        # Sigmoid case → single probability
        label = "♻️ Recyclable" if preds[0] > 0.5 else "🚯 Non-Recyclable"
    else:  
        # Softmax case → two probabilities
        label = "♻️ Recyclable" if np.argmax(preds) == 1 else "🚯 Non-Recyclable"

    return jsonify({'prediction': label, 'file_path': filepath})

if __name__ == "__main__":
    app.run(debug=True)
