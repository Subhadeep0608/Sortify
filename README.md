# ♻️ Sortify – Smart Waste Classification & Management

Sortify is a **Flask-based web application** designed to classify waste as **Recyclable** or **Non-Recyclable** using a trained Deep Learning model. It features a secure **user authentication system** (Sign Up / Login) and a modern, responsive UI styled with **Tailwind CSS**.

## 🚀 Features
- ✅ **Image Upload & Prediction**: Upload waste images for classification.  
- ✅ **Deep Learning Model**: Utilizes a pre-trained CNN model (`Sortify.h5`) for accurate waste classification.  
- ✅ **User Authentication**: Secure signup and login system using Flask sessions.  
- ✅ **Beautiful UI**: Responsive frontend powered by Tailwind CSS.  
- ✅ **Modular Project Structure**: Organized and maintainable codebase.

## 📂 Project Structure
```
Sortify/
├── app.py                    # Main Flask application
├── model/
│   └── Sortify.h5            # Pre-trained classification model
├── static/                   # Static files (CSS, JS, images)
│   ├── style.css
│   └── script.js
├── templates/                # HTML templates for frontend
│   ├── landing.html
│   ├── login.html
│   ├── signup.html
│   └── upload.html
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/Subhadeep0608/Sortify.git
cd Sortify
```

### 2️⃣ Install Dependencies
Ensure you have **Python 3.8+** installed. Then, install the required packages:
```bash
pip install -r requirements.txt
```

### 3️⃣ Run the Application
```bash
python app.py
```

### 4️⃣ Access the Application
Open your browser and navigate to:
```
http://127.0.0.1:5000/
```

## 🛠️ Requirements
See `requirements.txt` for the full list of Python dependencies. Key libraries include:
- Flask
- TensorFlow (for the CNN model)
- Other dependencies as listed in `requirements.txt`

## 📖 Usage
1. **Sign Up / Login**: Create an account or log in to access the waste classification feature.
2. **Upload Image**: Use the upload page to submit an image of waste.
3. **Get Results**: The model will classify the waste as **Recyclable** or **Non-Recyclable**.

## 🌟 Contributing
Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes and commit (`git commit -m "Add feature"`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a Pull Request.

## 📜