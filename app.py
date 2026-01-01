import os
from datetime import datetime, date
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, flash
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# --- CONFIGURATION ---
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super-secret-key-123') # Needed for flash messages

# CORS: Allow your specific frontend
CORS(app, resources={r"/*": {
    "origins": [
        "https://frontend-aimatrix.vercel.app", 
        "http://127.0.0.1:5500", 
        "http://localhost:5500"
    ]
}}, supports_credentials=True)

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

# --- API ROUTES (Frontend Connection) ---

@app.route('/')
def home():
    return jsonify({"status": "active", "message": "AIMatrix Commercial Backend Live"})

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
        return jsonify({'success': True, 'message': 'Message saved'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# *** RESTORED FEATURE: LIVE ANALYTICS ***
@app.route('/api/analytics', methods=['GET'])
def analytics():
    # 1. Get Total Messages
    total_messages = ContactMessage.query.count()
    
    # 2. Get Today's Messages
    today = date.today()
    todays_messages = ContactMessage.query.filter(ContactMessage.date >= datetime.combine(today, datetime.min.time())).count()
    
    # 3. Get Unique Emails
    unique_emails = db.session.query(ContactMessage.email).distinct().count()

    return jsonify({
        "success": True,
        "data": {
            "submissions": {
                "total": total_messages,
                "today": todays_messages,
                "unique_emails": unique_emails
            }
        }
    })

# --- ADMIN DASHBOARD (With Reply & Delete) ---

@app.route('/admin')
def admin_panel():
    messages = ContactMessage.query.order_by(ContactMessage.date.desc()).all()
    
    # HTML Template with Reply & Delete Actions
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AIMatrix Admin</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Poppins', sans-serif; background: #f1f5f9; margin: 0; padding: 40px; }
            .container { max-width: 1100px; margin: 0 auto; }
            .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
            h1 { color: #0f172a; margin: 0; font-size: 24px; }
            .card { background: white; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); overflow: hidden; }
            table { width: 100%; border-collapse: collapse; }
            th { background: #f8fafc; text-align: left; padding: 16px; font-size: 13px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }
            td { padding: 16px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #334155; vertical-align: top; }
            tr:last-child td { border-bottom: none; }
            .msg-text { max-width: 300px; color: #475569; }
            .date { color: #94a3b8; font-size: 12px; }
            .actions { display: flex; gap: 8px; }
            .btn { text-decoration: none; padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: 500; display: inline-flex; align-items: center; gap: 5px; border: none; cursor: pointer; transition: 0.2s; }
            .btn-reply { background: #eff6ff; color: #2563eb; }
            .btn-reply:hover { background: #dbeafe; }
            .btn-delete { background: #fef2f2; color: #ef4444; }
            .btn-delete:hover { background: #fee2e2; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1><i class="fas fa-inbox"></i> Inbox ({{ messages|length }})</h1>
                <a href="/" style="text-decoration:none; color:#64748b; font-size:14px;"><i class="fas fa-external-link-alt"></i> View Site</a>
            </div>
            
            <div class="card">
                <table>
                    <thead>
                        <tr>
                            <th>From</th>
                            <th>Message</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for msg in messages %}
                        <tr>
                            <td width="25%">
                                <strong>{{ msg.name }}</strong><br>
                                <span style="font-size:13px; color:#64748b;">{{ msg.email }}</span><br>
                                <span class="date">{{ msg.date.strftime('%b %d, %H:%M') }}</span>
                            </td>
                            <td class="msg-text">{{ msg.message }}</td>
                            <td width="20%">
                                <div class="actions">
                                    <a href="mailto:{{ msg.email }}?subject=Re: AIMatrix Inquiry&body=Hi {{ msg.name }},%0D%0A%0D%0AThanks for reaching out regarding: '{{ msg.message }}'..." class="btn btn-reply">
                                        <i class="fas fa-reply"></i> Reply
                                    </a>
                                    
                                    <form action="/admin/delete/{{ msg.id }}" method="POST" onsubmit="return confirm('Are you sure you want to delete this message?');">
                                        <button type="submit" class="btn btn-delete">
                                            <i class="fas fa-trash"></i> Delete
                                        </button>
                                    </form>
                                </div>
                            </td>
                        </tr>
                        {% else %}
                        <tr><td colspan="3" style="text-align:center; padding:40px; color:#94a3b8;">No messages found.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, messages=messages)

# *** RESTORED FEATURE: DELETE MESSAGE ***
@app.route('/admin/delete/<int:msg_id>', methods=['POST'])
def delete_message(msg_id):
    msg = ContactMessage.query.get(msg_id)
    if msg:
        db.session.delete(msg)
        db.session.commit()
    return redirect(url_for('admin_panel'))

# Initialize DB
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
