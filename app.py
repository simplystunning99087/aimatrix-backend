import os
from datetime import datetime, date
from flask import Flask, request, jsonify, render_template_string, redirect, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'secret-key')

# Allow your Vercel frontend
# CORS: Allow ALL origins (Fixes connection issues)
# CORS: You MUST list the specific URL to allow login/admin to work
CORS(app, resources={r"/*": {
    "origins": [
        "https://frontend-aimatrix.vercel.app",
        "https://frontend-aimatrix.vercel.app/",
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ]
}}, supports_credentials=True)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///aimatrix.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    message = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def home():
    return jsonify({"status": "Online"})

# --- 1. LIVE ANALYTICS ENDPOINT ---
@app.route('/api/analytics')
def analytics():
    # Fetch real counts from database
    total = ContactMessage.query.count()
    
    # Count today's messages
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_count = ContactMessage.query.filter(ContactMessage.date >= today_start).count()
    
    # Count unique emails
    unique_count = db.session.query(ContactMessage.email).distinct().count()

    return jsonify({
        "success": True,
        "data": {
            "submissions": {
                "total": total,
                "today": today_count,
                "unique_emails": unique_count
            }
        }
    })

# --- 2. CONTACT FORM ---
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
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# --- 3. ADMIN PANEL (Updated with Copy Button) ---
@app.route('/admin')
def admin_panel():
    messages = ContactMessage.query.order_by(ContactMessage.date.desc()).all()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AIMatrix Admin</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body { font-family: sans-serif; background: #f1f5f9; padding: 40px; }
            .card { background: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden; max-width: 1000px; margin: 0 auto; }
            table { width: 100%; border-collapse: collapse; }
            th { background: #f8fafc; text-align: left; padding: 15px; color: #64748b; font-size: 13px; text-transform: uppercase; }
            td { padding: 15px; border-bottom: 1px solid #e2e8f0; color: #334155; }
            .btn { padding: 5px 10px; border-radius: 5px; text-decoration: none; font-size: 12px; cursor: pointer; border: none; display: inline-flex; align-items: center; gap: 5px; }
            .btn-copy { background: #eff6ff; color: #2563eb; }
            .btn-delete { background: #fef2f2; color: #ef4444; }
        </style>
        <script>
            function copyEmail(email) {
                navigator.clipboard.writeText(email);
                alert('Email copied: ' + email);
            }
        </script>
    </head>
    <body>
        <div class="card">
            <table>
                <thead><tr><th>User</th><th>Message</th><th>Actions</th></tr></thead>
                <tbody>
                    {% for msg in messages %}
                    <tr>
                        <td width="25%">
                            <strong>{{ msg.name }}</strong><br>
                            <small>{{ msg.email }}</small><br>
                            <small style="color:#94a3b8">{{ msg.date.strftime('%Y-%m-%d %H:%M') }}</small>
                        </td>
                        <td>{{ msg.message }}</td>
                        <td width="20%">
                            <button onclick="copyEmail('{{ msg.email }}')" class="btn btn-copy"><i class="fas fa-copy"></i> Copy Email</button>
                            <form action="/admin/delete/{{ msg.id }}" method="POST" style="display:inline;">
                                <button type="submit" class="btn btn-delete" onclick="return confirm('Delete?')"><i class="fas fa-trash"></i></button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, messages=messages)

@app.route('/admin/delete/<int:msg_id>', methods=['POST'])
def delete_message(msg_id):
    msg = ContactMessage.query.get(msg_id)
    if msg:
        db.session.delete(msg)
        db.session.commit()
    return redirect('/admin')

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
