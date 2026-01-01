import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# --- CONFIGURATION ---
app = Flask(__name__)

# Allow requests from your Vercel Frontend and Localhost
CORS(app, resources={r"/*": {
    "origins": [
        "https://frontend-aimatrix.vercel.app", 
        "http://127.0.0.1:5500", 
        "http://localhost:5500"
    ]
}}, supports_credentials=True)

# Secret Key & Database
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
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
    return jsonify({"status": "active", "message": "AIMatrix Backend Online"})

# 1. REGISTER
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    hashed_pw = generate_password_hash(data.get('password'), method='pbkdf2:sha256')
    new_user = User(email=data.get('email'), name=data.get('name'), password=hashed_pw)
    
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
        return jsonify({'message': 'Login successful', 'user': {'name': user.name, 'email': user.email}})
    return jsonify({'error': 'Invalid credentials'}), 401

# 3. CONTACT FORM
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
        return jsonify({'success': True, 'message': 'Message received'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# --- NEW: ADMIN DASHBOARD ROUTE ---
@app.route('/admin')
def admin_panel():
    # Fetch all data from database
    users = User.query.order_by(User.created_at.desc()).all()
    messages = ContactMessage.query.order_by(ContactMessage.date.desc()).all()
    
    # HTML Template for the Dashboard
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AIMatrix Admin</title>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Poppins', sans-serif; background: #f4f6f8; padding: 40px; }
            .container { max-width: 1000px; margin: 0 auto; }
            h1 { color: #f43f5e; margin-bottom: 30px; }
            .card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 30px; }
            h2 { font-size: 1.2rem; margin-bottom: 20px; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; }
            table { width: 100%; border-collapse: collapse; }
            th { text-align: left; color: #666; font-size: 14px; padding: 10px; border-bottom: 1px solid #eee; }
            td { padding: 12px 10px; border-bottom: 1px solid #f9f9f9; color: #333; font-size: 14px; }
            .empty { color: #999; font-style: italic; }
            .badge { background: #e0f2fe; color: #0284c7; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 AIMatrix Admin</h1>
            
            <div class="card">
                <h2>📥 Recent Messages ({{ messages|length }})</h2>
                <table>
                    <thead>
                        <tr>
                            <th width="150">Date</th>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Message</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for msg in messages %}
                        <tr>
                            <td>{{ msg.date.strftime('%Y-%m-%d %H:%M') }}</td>
                            <td><strong>{{ msg.name }}</strong></td>
                            <td>{{ msg.email }}</td>
                            <td>{{ msg.message }}</td>
                        </tr>
                        {% else %}
                        <tr><td colspan="4" class="empty">No messages yet.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <div class="card">
                <h2>👥 Registered Users ({{ users|length }})</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Joined</th>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for user in users %}
                        <tr>
                            <td>{{ user.created_at.strftime('%Y-%m-%d') }}</td>
                            <td>{{ user.name }}</td>
                            <td>{{ user.email }}</td>
                            <td><span class="badge">Active</span></td>
                        </tr>
                        {% else %}
                        <tr><td colspan="4" class="empty">No users registered yet.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template, users=users, messages=messages)

# Initialize DB
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
