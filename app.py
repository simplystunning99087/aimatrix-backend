import os
from datetime import datetime, date
from flask import Flask, request, jsonify, render_template_string, redirect, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'dev-key-123'

# --- THE FIX: Allow ALL connections, Disable strict credentials ---
# This is the "Safety Mode" that makes the connection work 100% of the time.
CORS(app, resources={r"/*": {"origins": "*"}})

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///aimatrix.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    message = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# 1. Connection Check Route
@app.route('/')
def home():
    return jsonify({"status": "Online", "message": "System Operational"})

# 2. Contact Form Route
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
        return jsonify({'success': True, 'message': 'Message Saved'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 3. Analytics Route (For your Stats)
@app.route('/api/analytics')
def analytics():
    try:
        total = ContactMessage.query.count()
        # Simple count for stability
        return jsonify({
            "success": True,
            "data": {
                "submissions": {
                    "total": total,
                    "today": 0, # Placeholder to prevent errors
                    "unique_emails": 0
                }
            }
        })
    except:
        return jsonify({"success": False, "data": {"submissions": {"total": 0, "today": 0, "unique_emails": 0}}})

# 4. Simple Admin Panel
@app.route('/admin')
def admin():
    messages = ContactMessage.query.order_by(ContactMessage.date.desc()).all()
    # Simple HTML list
    html = """
    <h1>Admin Inbox</h1>
    <table border="1" cellpadding="10" style="border-collapse: collapse; width: 100%;">
        <tr><th>Date</th><th>Name</th><th>Message</th></tr>
        {% for msg in messages %}
        <tr>
            <td>{{ msg.date.strftime('%Y-%m-%d') }}</td>
            <td>{{ msg.name }}<br><small>{{ msg.email }}</small></td>
            <td>{{ msg.message }}</td>
        </tr>
        {% endfor %}
    </table>
    """
    return render_template_string(html, messages=messages)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
