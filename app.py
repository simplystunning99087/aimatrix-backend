import os
from datetime import datetime, date
from flask import Flask, request, jsonify, render_template_string, redirect, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# --- CONFIGURATION ---
app = Flask(__name__)
app.secret_key = 'admin-secret-key' # Required for sessions/security

# CORS: Keep this on "Allow All" to ensure your connection stays fixed
CORS(app, resources={r"/*": {"origins": "*"}})

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///aimatrix.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    message = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Unread') # New field

# --- API ROUTES (Frontend Connection) ---
@app.route('/')
def home():
    return jsonify({"status": "Online", "service": "AIMatrix Commercial Backend"})

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
        return jsonify({'success': True, 'message': 'Saved'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analytics')
def analytics():
    # Real-time stats for your frontend
    total = ContactMessage.query.count()
    today_start = datetime.combine(date.today(), datetime.min.time())
    today = ContactMessage.query.filter(ContactMessage.date >= today_start).count()
    unique = db.session.query(ContactMessage.email).distinct().count()
    
    return jsonify({
        "success": True,
        "data": { "submissions": { "total": total, "today": today, "unique_emails": unique } }
    })

# --- ADVANCED ADMIN DASHBOARD ---
@app.route('/admin')
def admin_panel():
    messages = ContactMessage.query.order_by(ContactMessage.date.desc()).all()
    total = len(messages)
    today_count = sum(1 for m in messages if m.date.date() == date.today())
    
    # Professional Tailwind CSS Dashboard Template
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AIMatrix | Command Center</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            body { font-family: 'Inter', sans-serif; background-color: #f3f4f6; }
            .glass { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); }
        </style>
    </head>
    <body>
        <div class="flex h-screen overflow-hidden">
            <aside class="w-64 bg-slate-900 text-white hidden md:flex flex-col">
                <div class="p-6 text-center border-b border-slate-800">
                    <h1 class="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-pink-500 to-violet-500">AIMatrix</h1>
                    <p class="text-xs text-slate-400 mt-1">ADMIN CONSOLE</p>
                </div>
                <nav class="flex-1 p-4 space-y-2">
                    <a href="#" class="flex items-center gap-3 px-4 py-3 bg-slate-800 rounded-lg text-blue-400 font-medium">
                        <i class="fas fa-inbox w-5"></i> Inbox
                    </a>
                    <a href="/" target="_blank" class="flex items-center gap-3 px-4 py-3 text-slate-400 hover:bg-slate-800 hover:text-white rounded-lg transition">
                        <i class="fas fa-external-link-alt w-5"></i> Live Site
                    </a>
                </nav>
                <div class="p-4 border-t border-slate-800">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-pink-500 to-violet-500 flex items-center justify-center font-bold">A</div>
                        <div class="text-sm">
                            <p class="font-medium">Administrator</p>
                            <p class="text-xs text-slate-500">Super User</p>
                        </div>
                    </div>
                </div>
            </aside>

            <main class="flex-1 flex flex-col overflow-hidden">
                <header class="bg-white border-b border-gray-200 p-6 flex justify-between items-center">
                    <h2 class="text-2xl font-bold text-gray-800">Messages Inbox</h2>
                    <div class="flex gap-4">
                        <input type="text" id="searchInput" placeholder="Search emails..." class="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 w-64 text-sm">
                        <button onclick="window.location.reload()" class="p-2 text-gray-500 hover:text-blue-600 transition"><i class="fas fa-sync-alt"></i></button>
                    </div>
                </header>

                <div class="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div class="bg-white p-5 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4">
                        <div class="w-12 h-12 rounded-full bg-blue-50 flex items-center justify-center text-blue-600 text-xl"><i class="fas fa-envelope"></i></div>
                        <div>
                            <p class="text-sm text-gray-500 font-medium">Total Messages</p>
                            <h3 class="text-2xl font-bold text-gray-800">{{ total }}</h3>
                        </div>
                    </div>
                    <div class="bg-white p-5 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4">
                        <div class="w-12 h-12 rounded-full bg-green-50 flex items-center justify-center text-green-600 text-xl"><i class="fas fa-calendar-day"></i></div>
                        <div>
                            <p class="text-sm text-gray-500 font-medium">New Today</p>
                            <h3 class="text-2xl font-bold text-gray-800">{{ today }}</h3>
                        </div>
                    </div>
                    <div class="bg-white p-5 rounded-xl shadow-sm border border-gray-100 flex items-center gap-4">
                        <div class="w-12 h-12 rounded-full bg-purple-50 flex items-center justify-center text-purple-600 text-xl"><i class="fas fa-bolt"></i></div>
                        <div>
                            <p class="text-sm text-gray-500 font-medium">System Status</p>
                            <h3 class="text-lg font-bold text-green-500">Operational</h3>
                        </div>
                    </div>
                </div>

                <div class="flex-1 overflow-auto p-6 pt-0">
                    <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                        <table class="w-full text-left border-collapse">
                            <thead class="bg-gray-50 text-gray-500 text-xs uppercase font-semibold">
                                <tr>
                                    <th class="p-4">Sender Info</th>
                                    <th class="p-4">Message Snippet</th>
                                    <th class="p-4">Date</th>
                                    <th class="p-4 text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody class="text-sm divide-y divide-gray-100">
                                {% for msg in messages %}
                                <tr class="hover:bg-gray-50 transition group">
                                    <td class="p-4">
                                        <p class="font-bold text-gray-800">{{ msg.name }}</p>
                                        <p class="text-blue-500 text-xs">{{ msg.email }}</p>
                                    </td>
                                    <td class="p-4 text-gray-600 max-w-xs truncate cursor-pointer hover:text-blue-600" onclick="openModal('{{ msg.name }}', '{{ msg.message }}')">
                                        {{ msg.message }}
                                    </td>
                                    <td class="p-4 text-gray-400 text-xs whitespace-nowrap">
                                        {{ msg.date.strftime('%b %d, %H:%M') }}
                                    </td>
                                    <td class="p-4 text-right">
                                        <div class="flex justify-end gap-2">
                                            <button onclick="openModal('{{ msg.name }}', '{{ msg.message }}')" class="p-2 rounded-lg bg-gray-100 text-gray-600 hover:bg-blue-100 hover:text-blue-600 transition" title="View Full Message">
                                                <i class="fas fa-eye"></i>
                                            </button>
                                            
                                            <a href="mailto:{{ msg.email }}?subject=Re: Inquiry from {{ msg.name }}&body=Hi {{ msg.name }},%0D%0A%0D%0AWe received your message: '{{ msg.message }}'%0D%0A%0D%0A..." class="p-2 rounded-lg bg-gray-100 text-gray-600 hover:bg-green-100 hover:text-green-600 transition" title="Reply via Email">
                                                <i class="fas fa-reply"></i>
                                            </a>

                                            <form action="/admin/delete/{{ msg.id }}" method="POST" onsubmit="return confirm('Permanently delete message from {{ msg.name }}?')">
                                                <button type="submit" class="p-2 rounded-lg bg-gray-100 text-gray-600 hover:bg-red-100 hover:text-red-600 transition" title="Delete">
                                                    <i class="fas fa-trash"></i>
                                                </button>
                                            </form>
                                        </div>
                                    </td>
                                </tr>
                                {% else %}
                                <tr>
                                    <td colspan="4" class="p-10 text-center text-gray-400 italic">No messages found.</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </main>
        </div>

        <div id="msgModal" class="fixed inset-0 bg-black/50 hidden items-center justify-center z-50 backdrop-blur-sm">
            <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 transform transition-all scale-95 opacity-0" id="modalContent">
                <div class="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50 rounded-t-2xl">
                    <h3 class="font-bold text-lg text-gray-800" id="modalTitle">Message</h3>
                    <button onclick="closeModal()" class="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
                </div>
                <div class="p-8">
                    <p class="text-gray-600 leading-relaxed text-lg" id="modalBody">...</p>
                </div>
                <div class="p-6 border-t border-gray-100 flex justify-end">
                    <button onclick="closeModal()" class="px-6 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-900 transition">Close</button>
                </div>
            </div>
        </div>

        <script>
            // MODAL LOGIC
            const modal = document.getElementById('msgModal');
            const content = document.getElementById('modalContent');
            
            function openModal(name, message) {
                document.getElementById('modalTitle').innerText = 'From: ' + name;
                document.getElementById('modalBody').innerText = message;
                modal.classList.remove('hidden');
                modal.classList.add('flex');
                // Animation
                setTimeout(() => {
                    content.classList.remove('scale-95', 'opacity-0');
                    content.classList.add('scale-100', 'opacity-100');
                }, 10);
            }

            function closeModal() {
                content.classList.remove('scale-100', 'opacity-100');
                content.classList.add('scale-95', 'opacity-0');
                setTimeout(() => {
                    modal.classList.add('hidden');
                    modal.classList.remove('flex');
                }, 200);
            }

            // SEARCH FILTER
            document.getElementById('searchInput').addEventListener('keyup', function(e) {
                const term = e.target.value.toLowerCase();
                const rows = document.querySelectorAll('tbody tr');
                
                rows.forEach(row => {
                    const text = row.innerText.toLowerCase();
                    row.style.display = text.includes(term) ? '' : 'none';
                });
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html, messages=messages, total=total, today=today_count)

@app.route('/admin/delete/<int:msg_id>', methods=['POST'])
def delete_message(msg_id):
    msg = ContactMessage.query.get(msg_id)
    if msg:
        db.session.delete(msg)
        db.session.commit()
    return redirect('/admin')

# Initialize
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
