import os
import json
import razorpay
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# --- CONFIGURATION ---
app = Flask(__name__)
CORS(app, supports_credentials=True) # Allows frontend to send cookies/auth headers

# Secret keys (Set these in Render Environment Variables later)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-dev-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///aimatrix.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Database & Auth
db = SQLAlchemy(app)
login_manager = LoginManager(app)

# Razorpay Client Setup
# Get these keys from https://dashboard.razorpay.com/app/keys
razorpay_client = razorpay.Client(
    auth=(os.environ.get('RZP_KEY_ID'), os.environ.get('RZP_KEY_SECRET'))
)

# --- DATABASE MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120))
    plan = db.Column(db.String(50), default='free') # free, starter, growth, enterprise
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    message = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120))
    order_id = db.Column(db.String(100))
    payment_id = db.Column(db.String(100))
    amount = db.Column(db.Integer)
    status = db.Column(db.String(20)) # created, paid, failed

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROUTES ---

@app.route('/')
def home():
    return "AIMatrix Commercial Backend is Running"

# 1. AUTHENTICATION
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    hashed_pw = generate_password_hash(data.get('password'), method='pbkdf2:sha256')
    new_user = User(email=data.get('email'), name=data.get('name'), password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Registration successful'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data.get('email')).first()
    
    if user and check_password_hash(user.password, data.get('password')):
        login_user(user)
        return jsonify({
            'message': 'Login successful',
            'user': {'email': user.email, 'name': user.name, 'plan': user.plan}
        })
    return jsonify({'error': 'Invalid email or password'}), 401

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out'})

# 2. CONTACT FORM (Restored functionality)
@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.json
    new_msg = ContactMessage(
        name=data.get('name'),
        email=data.get('email'),
        message=data.get('message')
    )
    db.session.add(new_msg)
    db.session.commit()
    return jsonify({'message': 'Message sent successfully!'})

# 3. PAYMENTS (Razorpay)
@app.route('/api/create-order', methods=['POST'])
def create_order():
    # In a real app, use @login_required here
    amount = request.json.get('amount') # Amount in paise
    currency = "INR"
    
    data = { "amount": amount, "currency": currency, "receipt": "order_rcptid_11" }
    order = razorpay_client.order.create(data=data)
    
    # Save order to DB
    # (Optional: Link this to the current logged-in user)
    
    return jsonify(order)

@app.route('/api/verify-payment', methods=['POST'])
def verify_payment():
    data = request.json
    try:
        # Verify signature
        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature']
        })
        
        # If successful, upgrade user plan here
        # user = User.query.filter_by(email=...).first()
        # user.plan = 'growth'
        # db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Payment Verified'})
    except Exception as e:
        return jsonify({'status': 'failure', 'error': str(e)}), 400

# Create DB tables if they don't exist
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
