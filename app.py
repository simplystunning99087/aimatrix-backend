import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# --- CONFIGURATION ---
app = Flask(__name__)

# CORS: Allow requests from your frontend
# Replace '*' with 'https://frontend-aimatrix.vercel.app' for better security in production
# ALLOW your Vercel URL and Localhost (for testing)
CORS(app, resources={r"/*": {
    "origins": [
        "https://frontend-aimatrix.vercel.app", 
        "http://127.0.0.1:5500", 
        "http://localhost:5500"
    ]
}}, supports_credentials=True)
# Secret Key (Set this in Render Environment Variables)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')

# Database Config (Uses SQLite locally, Postgres on Render if configured)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///aimatrix.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)

# --- DATABASE MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    message = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- API ROUTES ---

@app.route('/')
def home():
    return jsonify({"status": "active", "message": "AIMatrix Commercial Backend Ready"})

# 1. REGISTER
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    
    # Check if user exists
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    # Create new user
    hashed_pw = generate_password_hash(data.get('password'), method='pbkdf2:sha256')
    new_user = User(
        email=data.get('email'),
        name=data.get('name'),
        password=hashed_pw
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 2. LOGIN
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data.get('email')).first()
    
    if user and check_password_hash(user.password, data.get('password')):
        login_user(user)
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email
            }
        })
    
    return jsonify({'error': 'Invalid email or password'}), 401

# 3. LOGOUT
@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'})

# 4. CONTACT FORM (Commercial Lead Gen)
@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.json
    try:
        new_msg = ContactMessage(
            name=data.get('name'),
            email=data.get('email'),
            message=data.get('message')
        )
        db.session.add(new_msg)
        db.session.commit()
        return jsonify({'message': 'Message received. We will contact you shortly.'}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to save message'}), 500

# 5. PROTECTED DASHBOARD DATA
@app.route('/api/user-data', methods=['GET'])
@login_required
def get_user_data():
    return jsonify({
        'name': current_user.name,
        'email': current_user.email,
        'account_status': 'Active'
    })

# Initialize DB
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
