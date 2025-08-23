♻️ Sortify – Smart Waste Classification & Management
Sortify is a Flask-based web application designed to classify waste as Recyclable or Non-Recyclable using a trained Deep Learning model. It features a secure user authentication system (Sign Up / Login) and a modern, responsive UI styled with Tailwind CSS.
🚀 Features

✅ Image Upload & Prediction: Upload an image of waste to receive classification results.
✅ Deep Learning Model: Utilizes a trained CNN model (Sortify.h5) for accurate waste classification.
✅ User Authentication: Secure signup and login functionality using Flask sessions.
✅ Beautiful UI: Responsive and modern frontend powered by Tailwind CSS.
✅ Modular Project Structure: Organized codebase for easy maintenance and scalability.

📂 Project Structure
Sortify/
├── app.py                 # Main Flask application
├── model/
│   └── Sortify.h5         # Pre-trained classification model
├── static/                # Static files (CSS, JS, images)
│   ├── style.css
│   └── script.js
├── templates/             # HTML templates for frontend
│   ├── landing.html
│   ├── login.html
│   ├── signup.html
│   └── upload.html
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation

⚙️ Installation & Setup
1️⃣ Clone the Repository
git clone https://github.com/Subhadeep0608/Sortify.git
cd Sortify

2️⃣ Install Dependencies
Ensure you have Python 3.8+ installed. Then, install the required packages:
pip install -r requirements.txt

3️⃣ Run the Application
python app.py

4️⃣ Access the Application
Open your browser and navigate to:
http://127.0.0.1:5000/

🛠️ Usage

Sign Up / Login: Create an account or log in to access the application.
Upload Waste Image: Use the upload feature to submit an image of waste.
View Results: The application will classify the waste as Recyclable or Non-Recyclable.

📦 Dependencies
Listed in requirements.txt. Key dependencies include:

Flask
TensorFlow (for the CNN model)
NumPy
Pillow

🤝 Contributing
Contributions are welcome! Please follow these steps:

Fork the repository.
Create a new branch (git checkout -b feature-branch).
Make your changes and commit (git commit -m 'Add new feature').
Push to the branch (git push origin feature-branch).
Create a Pull Request.

📜 License
This project is licensed under the MIT License.
📬 Contact
For questions or feedback, reach out to the project maintainer at:

GitHub: Subhadeep0608
