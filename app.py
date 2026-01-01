import os
import razorpay
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from models import db, User, Order

app = Flask(__name__)
CORS(app) # Allow frontend to talk to backend

# Config
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///aimatrix.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)

# Razorpay Client
client = razorpay.Client(auth=(os.environ.get('RZP_KEY'), os.environ.get('RZP_SECRET')))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- AUTH ROUTES ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already exists"}), 400
    
    hashed_pw = generate_password_hash(data['password'], method='pbkdf2:sha256')
    new_user = User(email=data['email'], name=data['name'], password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User created successfully"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if user and check_password_hash(user.password, data['password']):
        login_user(user)
        return jsonify({"message": "Login successful", "user": user.name, "plan": user.plan_type})
    return jsonify({"error": "Invalid credentials"}), 401

# --- PAYMENT ROUTES (Razorpay) ---
@app.route('/api/create-order', methods=['POST'])
@login_required # Only logged in users can buy
def create_order():
    amount = request.json.get('amount') # Amount in paise (e.g., 2999900 for ₹29,999)
    data = { "amount": amount, "currency": "INR", "receipt": "order_rcptid_11" }
    payment = client.order.create(data=data)
    
    # Save pending order
    new_order = Order(order_id=payment['id'], user_email=current_user.email, amount=amount, status='pending')
    db.session.add(new_order)
    db.session.commit()
    
    return jsonify(payment)

@app.route('/api/verify-payment', methods=['POST'])
def verify_payment():
    data = request.json
    # Verify signature securely using Razorpay utility
    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature']
        })
        # Update user plan
        order = Order.query.filter_by(order_id=data['razorpay_order_id']).first()
        order.status = 'paid'
        user = User.query.filter_by(email=order.user_email).first()
        user.plan_type = 'growth' # Logic to decide plan based on amount
        db.session.commit()
        return jsonify({"status": "success"})
    except:
        return jsonify({"status": "failure"}), 400

# Initialize DB
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
