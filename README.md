# ♻️ Sortify – Smart Waste Classification & Management

Sortify is a **Flask-based web application** that helps classify waste as **Recyclable** or **Non-Recyclable** using a trained Deep Learning model.  
It also includes a **user authentication system (Sign Up / Login)** and a clean, modern UI with Tailwind CSS.

---

## 🚀 Features
- ✅ **Image Upload & Prediction** – Upload an image of waste and get classification results.  
- ✅ **Deep Learning Model** – Trained CNN model (`Sortify.h5`) for waste classification.  
- ✅ **User Authentication** – Secure signup/login using Flask sessions.  
- ✅ **Beautiful UI** – Tailwind-powered responsive frontend.  
- ✅ **Modular Project Structure** – Easy to extend and maintain.  

---

## 📂 Project Structure
Sortify/
│── app.py # Main Flask app
│── model/Sortify.h5 # Pre-trained classification model
│── static/ # Static files (CSS, JS, images)
│ ├── style.css
│ └── script.js
│── templates/ # Frontend templates
│ ├── landing.html
│ ├── login.html
│ ├── signup.html
│ └── upload.html
│── requirements.txt # Python dependencies
│── README.md # Project documentation


---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/Subhadeep0608/Sortify.git
cd Sortify
un the Application
python app.py


Now open your browser and go to 👉 http://127.0.0.1:5000/