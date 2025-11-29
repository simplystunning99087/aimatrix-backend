from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime, timedelta
import csv
from io import StringIO
import time
from functools import wraps
import shutil
import requests
import json

app = Flask(__name__)
CORS(app)

# ==================== CONFIGURATION ====================
APP_NAME = "AIMatrix Backend"
VERSION = "2.1.0"
MAX_SUBMISSIONS_PER_MINUTE = 10

# ==================== DATABASE SETUP ====================
def get_db_connection():
    conn = sqlite3.connect('contact_submissions.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            ip_address TEXT,
            status TEXT DEFAULT 'new',
            priority TEXT DEFAULT 'normal',
            tags TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id INTEGER,
            email_type TEXT,
            status TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (submission_id) REFERENCES contact_submissions (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT,
            details TEXT,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# ==================== EMAIL SERVICE ====================
def send_email_notification(submission_data, email_type="new_submission"):
    """Send email notifications using Resend.com"""
    try:
        RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
        
        if not RESEND_API_KEY:
            print("📧 Email service not configured. Set RESEND_API_KEY environment variable.")
            log_system_action("email_skipped", f"No API key for {email_type}")
            return False
        
        if email_type == "new_submission":
            subject = f"🎯 New Lead: {submission_data['name']}"
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .container {{ max-width: 600px; margin: 0 auto; }}
                    .header {{ background: linear-gradient(135deg, #f43f5e, #e11d48); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ padding: 20px; background: #f8fafc; }}
                    .field {{ margin: 15px 0; }}
                    .label {{ font-weight: bold; color: #64748b; }}
                    .admin-link {{ display: inline-block; padding: 10px 20px; background: #f43f5e; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🚀 New Contact Form Submission</h1>
                    </div>
                    <div class="content">
                        <div class="field">
                            <span class="label">Name:</span> {submission_data['name']}
                        </div>
                        <div class="field">
                            <span class="label">Email:</span> {submission_data['email']}
                        </div>
                        <div class="field">
                            <span class="label">Message:</span><br>
                            {submission_data['message']}
                        </div>
                        <div class="field">
                            <span class="label">Time:</span> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                        </div>
                        <div class="field">
                            <span class="label">IP Address:</span> {submission_data.get('ip_address', 'N/A')}
                        </div>
                        <a href="https://aimatrix-backend-6t9i.onrender.com/admin" class="admin-link">
                            📊 View in Admin Dashboard
                        </a>
                    </div>
                </div>
            </body>
            </html>
            """
        else:
            return False
        
        email_data = {
            "from": "AIMatrix <notifications@aimatrix.tryrelay.cc>",
            "to": ["manivelmtss@gmail.com"],
            "subject": subject,
            "html": html_content
        }
        
        response = requests.post(
            'https://api.resend.com/emails',
            headers={'Authorization': f'Bearer {RESEND_API_KEY}', 'Content-Type': 'application/json'},
            json=email_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Email sent successfully via Resend")
            log_email(submission_data.get('id'), email_type, 'sent')
            return True
        else:
            print(f"❌ Email failed: {response.status_code} - {response.text}")
            log_email(submission_data.get('id'), email_type, 'failed')
            return False
            
    except Exception as e:
        print(f"Email error: {e}")
        log_email(submission_data.get('id'), email_type, 'error')
        return False

def log_email(submission_id, email_type, status):
    """Log email sending attempts"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO email_logs (submission_id, email_type, status) VALUES (?, ?, ?)',
            (submission_id, email_type, status)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Email logging error: {e}")

def log_system_action(action, details, ip_address=None):
    """Log system actions for audit trail"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO system_logs (action, details, ip_address) VALUES (?, ?, ?)',
            (action, details, ip_address)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"System logging error: {e}")

# ==================== ENHANCED ANALYTICS ====================
@app.route('/api/analytics/advanced', methods=['GET'])
def advanced_analytics():
    """Advanced analytics with charts data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Time-based analytics
        cursor.execute('''
            SELECT 
                DATE(submitted_at) as date,
                COUNT(*) as count,
                COUNT(DISTINCT email) as unique_emails
            FROM contact_submissions 
            WHERE submitted_at >= DATE('now', '-30 days')
            GROUP BY DATE(submitted_at)
            ORDER BY date
        ''')
        daily_analytics = cursor.fetchall()
        
        # Status analytics
        cursor.execute('''
            SELECT 
                status,
                COUNT(*) as count,
                ROUND(AVG(LENGTH(message)), 2) as avg_message_length
            FROM contact_submissions 
            GROUP BY status
        ''')
        status_analytics = cursor.fetchall()
        
        # Hourly distribution
        cursor.execute('''
            SELECT 
                strftime('%H', submitted_at) as hour,
                COUNT(*) as count
            FROM contact_submissions 
            GROUP BY hour
            ORDER BY hour
        ''')
        hourly_analytics = cursor.fetchall()
        
        # Email performance
        cursor.execute('''
            SELECT 
                email_type,
                status,
                COUNT(*) as count
            FROM email_logs 
            GROUP BY email_type, status
        ''')
        email_analytics = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'daily_trends': [dict(row) for row in daily_analytics],
                'status_breakdown': [dict(row) for row in status_analytics],
                'hourly_distribution': [dict(row) for row in hourly_analytics],
                'email_performance': [dict(row) for row in email_analytics]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== ENHANCED SUBMISSIONS MANAGEMENT ====================
@app.route('/api/submissions/bulk', methods=['POST'])
def bulk_update_submissions():
    """Bulk update submissions"""
    try:
        data = request.get_json()
        submission_ids = data.get('submission_ids', [])
        action = data.get('action')
        
        if not submission_ids or not action:
            return jsonify({'success': False, 'error': 'Missing submission_ids or action'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if action == 'delete':
            placeholders = ','.join('?' * len(submission_ids))
            cursor.execute(f'DELETE FROM contact_submissions WHERE id IN ({placeholders})', submission_ids)
            log_system_action('bulk_delete', f'Deleted {len(submission_ids)} submissions')
        elif action in ['read', 'archived', 'replied']:
            placeholders = ','.join('?' * len(submission_ids))
            cursor.execute(f'UPDATE contact_submissions SET status = ? WHERE id IN ({placeholders})', [action] + submission_ids)
            log_system_action('bulk_update', f'Updated {len(submission_ids)} submissions to {action}')
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'Bulk {action} completed'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/submissions/<int:submission_id>/priority', methods=['PUT'])
def update_submission_priority(submission_id):
    """Update submission priority"""
    try:
        data = request.get_json()
        priority = data.get('priority', 'normal')
        
        valid_priorities = ['low', 'normal', 'high', 'urgent']
        if priority not in valid_priorities:
            return jsonify({'success': False, 'error': f'Invalid priority. Must be one of: {valid_priorities}'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE contact_submissions SET priority = ? WHERE id = ?',
            (priority, submission_id)
        )
        conn.commit()
        conn.close()
        
        log_system_action('priority_update', f'Submission {submission_id} priority set to {priority}')
        
        return jsonify({'success': True, 'message': f'Priority updated to {priority}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/submissions/<int:submission_id>/tags', methods=['PUT'])
def update_submission_tags(submission_id):
    """Update submission tags"""
    try:
        data = request.get_json()
        tags = data.get('tags', [])
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE contact_submissions SET tags = ? WHERE id = ?',
            (json.dumps(tags), submission_id)
        )
        conn.commit()
        conn.close()
        
        log_system_action('tags_update', f'Submission {submission_id} tags updated')
        
        return jsonify({'success': True, 'message': 'Tags updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== SYSTEM ENDPOINTS ====================
@app.route('/api/system/logs')
def get_system_logs():
    """Get system logs"""
    try:
        limit = request.args.get('limit', 100)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM system_logs 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        logs = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {'logs': [dict(row) for row in logs]}
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/health')
def system_health():
    """Comprehensive system health check"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Database stats
        cursor.execute('SELECT COUNT(*) as total FROM contact_submissions')
        total_submissions = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as today FROM contact_submissions WHERE DATE(submitted_at) = DATE("now")')
        today_submissions = cursor.fetchone()['today']
        
        cursor.execute('SELECT COUNT(*) as email_logs FROM email_logs')
        email_logs_count = cursor.fetchone()['email_logs']
        
        # Performance metrics
        cursor.execute('SELECT COUNT(*) as pending FROM contact_submissions WHERE status = "new"')
        pending_submissions = cursor.fetchone()['pending']
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'metrics': {
                    'total_submissions': total_submissions,
                    'today_submissions': today_submissions,
                    'pending_submissions': pending_submissions,
                    'email_logs': email_logs_count,
                    'uptime': '100%'
                },
                'services': {
                    'database': 'connected',
                    'email_service': 'configured' if os.environ.get('RESEND_API_KEY') else 'not_configured',
                    'api': 'operational'
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== EXISTING ENDPOINTS (Enhanced) ====================
@app.route('/health')
def health_check():
    return jsonify({
        "success": True,
        "message": "Service is healthy",
        "timestamp": datetime.now().isoformat(),
        "version": VERSION
    })

@app.route('/')
def home():
    return jsonify({
        "success": True,
        "message": f"{APP_NAME} is running",
        "version": VERSION,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/contact', methods=['POST'])
def contact_submit():
    try:
        data = request.get_json()
        
        if not data or not data.get('name') or not data.get('email') or not data.get('message'):
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO contact_submissions (name, email, message, ip_address)
            VALUES (?, ?, ?, ?)
        ''', (data['name'], data['email'], data['message'], ip_address))
        conn.commit()
        
        submission_id = cursor.lastrowid
        conn.close()
        
        # Send email notification
        send_email_notification({
            'id': submission_id,
            'name': data['name'],
            'email': data['email'],
            'message': data['message'],
            'ip_address': ip_address
        })
        
        log_system_action('new_submission', f'New submission from {data["email"]}', ip_address)
        
        return jsonify({
            "success": True,
            "message": "Contact form submitted successfully",
            "submission_id": submission_id
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/submissions', methods=['GET'])
def get_submissions():
    try:
        status_filter = request.args.get('status', 'all')
        priority_filter = request.args.get('priority', 'all')
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM contact_submissions WHERE 1=1'
        params = []
        
        if status_filter != 'all':
            query += ' AND status = ?'
            params.append(status_filter)
            
        if priority_filter != 'all':
            query += ' AND priority = ?'
            params.append(priority_filter)
            
        query += ' ORDER BY submitted_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        submissions = cursor.fetchall()
        conn.close()
        
        submissions_list = []
        for row in submissions:
            submission = dict(row)
            submission['tags'] = json.loads(submission['tags']) if submission['tags'] else []
            submissions_list.append(submission)
        
        return jsonify({
            "success": True,
            "data": {"submissions": submissions_list}
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/analytics', methods=['GET'])
def analytics():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as total FROM contact_submissions')
        total = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as today FROM contact_submissions WHERE DATE(submitted_at) = DATE("now")')
        today = cursor.fetchone()['today']
        
        cursor.execute('SELECT COUNT(*) as this_week FROM contact_submissions WHERE submitted_at >= DATE("now", "-7 days")')
        this_week = cursor.fetchone()['this_week']
        
        cursor.execute('SELECT COUNT(DISTINCT email) as unique_emails FROM contact_submissions')
        unique_emails = cursor.fetchone()['unique_emails']
        
        cursor.execute('SELECT status, COUNT(*) as count FROM contact_submissions GROUP BY status')
        status_data = cursor.fetchall()
        status_distribution = {row['status']: row['count'] for row in status_data}
        
        cursor.execute('SELECT priority, COUNT(*) as count FROM contact_submissions GROUP BY priority')
        priority_data = cursor.fetchall()
        priority_distribution = {row['priority']: row['count'] for row in priority_data}
        
        conn.close()
        
        return jsonify({
            "success": True,
            "data": {
                "submissions": {
                    "total": total,
                    "today": today,
                    "this_week": this_week,
                    "unique_emails": unique_emails
                },
                "status_distribution": status_distribution,
                "priority_distribution": priority_distribution
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== ADMIN DASHBOARD ====================
@app.route('/admin')
def serve_admin():
    """Serve the enhanced admin dashboard"""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard - AIMatrix</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --primary: #f43f5e;
            --dark: #0f172a;
            --muted: #6b7280;
            --bg: #f8fafc;
            --card: #ffffff;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --info: #3b82f6;
        }
        
        body { 
            font-family: 'Poppins', sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: var(--bg); 
            color: var(--dark); 
        }
        
        .container { 
            max-width: 1400px; 
            margin: 0 auto; 
        }
        
        .header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 30px; 
            flex-wrap: wrap;
            gap: 20px;
        }
        
        .stats { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; 
            margin-bottom: 30px; 
        }
        
        .stat-card { 
            background: white; 
            padding: 25px; 
            border-radius: 12px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
            text-align: center; 
            border-left: 4px solid var(--primary);
        }
        
        .stat-number { 
            font-size: 2.5em; 
            font-weight: 700; 
            color: var(--primary); 
            margin: 10px 0; 
        }
        
        .controls {
            display: flex;
            gap: 15px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .btn-primary { background: var(--primary); color: white; }
        .btn-success { background: var(--success); color: white; }
        .btn-danger { background: var(--danger); color: white; }
        .btn-warning { background: var(--warning); color: white; }
        .btn-info { background: var(--info); color: white; }
        
        .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .submissions-grid {
            display: grid;
            gap: 15px;
        }
        
        .submission-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border-left: 4px solid var(--success);
        }
        
        .submission-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 10px;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .submission-meta {
            color: var(--muted);
            font-size: 12px;
            margin: 5px 0;
        }
        
        .submission-actions {
            display: flex;
            gap: 10px;
            margin-top: 15px;
            flex-wrap: wrap;
        }
        
        .status-badge, .priority-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .status-new { background: #dbeafe; color: #1e40af; }
        .status-read { background: #dcfce7; color: #166534; }
        .status-archived { background: #f3f4f6; color: #374151; }
        .status-replied { background: #fef3c7; color: #92400e; }
        
        .priority-low { background: #d1fae5; color: #065f46; }
        .priority-normal { background: #dbeafe; color: #1e40af; }
        .priority-high { background: #fef3c7; color: #92400e; }
        .priority-urgent { background: #fee2e2; color: #991b1b; }
        
        .loading { 
            text-align: center; 
            padding: 40px; 
            color: var(--muted); 
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: var(--muted);
        }
        
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        
        .alert-success { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
        .alert-error { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
        
        .system-status {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .status-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #f1f5f9;
        }
        
        .tab-container {
            margin: 20px 0;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .tab {
            padding: 10px 20px;
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .tab.active {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .bulk-actions {
            background: #f8fafc;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            display: none;
        }
        
        .checkbox-item {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 5px 0;
        }
        
        @media (max-width: 768px) {
            .header { flex-direction: column; align-items: flex-start; }
            .stats { grid-template-columns: 1fr 1fr; }
            .dashboard-grid { grid-template-columns: 1fr; }
            .submission-actions { flex-direction: column; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-rocket"></i> AIMatrix Admin Dashboard v2.1</h1>
            <div class="controls">
                <button class="btn btn-primary" onclick="loadDashboard()"><i class="fas fa-sync-alt"></i> Refresh</button>
                <button class="btn btn-success" onclick="exportData()"><i class="fas fa-download"></i> Export CSV</button>
                <button class="btn btn-info" onclick="showSystemHealth()"><i class="fas fa-heartbeat"></i> System Health</button>
                <button class="btn btn-warning" onclick="showAdvancedAnalytics()"><i class="fas fa-chart-bar"></i> Analytics</button>
            </div>
        </div>
        
        <div id="alert-container"></div>
        <div id="system-health" class="system-status" style="display: none;"></div>
        
        <div class="tab-container">
            <div class="tabs">
                <div class="tab active" onclick="switchTab('overview')">📊 Overview</div>
                <div class="tab" onclick="switchTab('submissions')">📨 Submissions</div>
                <div class="tab" onclick="switchTab('analytics')">📈 Analytics</div>
                <div class="tab" onclick="switchTab('system')">⚙️ System</div>
            </div>
            
            <div id="tab-overview" class="tab-content active">
                <div class="stats" id="stats">
                    <div class="loading">Loading analytics...</div>
                </div>
                
                <div class="dashboard-grid">
                    <div class="chart-container">
                        <h3><i class="fas fa-chart-line"></i> Submission Trends</h3>
                        <canvas id="trendsChart" width="400" height="200"></canvas>
                    </div>
                    <div class="chart-container">
                        <h3><i class="fas fa-chart-pie"></i> Status Distribution</h3>
                        <canvas id="statusChart" width="400" height="200"></canvas>
                    </div>
                </div>
            </div>
            
            <div id="tab-submissions" class="tab-content">
                <div class="controls">
                    <select id="status-filter" onchange="loadSubmissions()">
                        <option value="all">All Status</option>
                        <option value="new">New</option>
                        <option value="read">Read</option>
                        <option value="replied">Replied</option>
                        <option value="archived">Archived</option>
                    </select>
                    <select id="priority-filter" onchange="loadSubmissions()">
                        <option value="all">All Priority</option>
                        <option value="low">Low</option>
                        <option value="normal">Normal</option>
                        <option value="high">High</option>
                        <option value="urgent">Urgent</option>
                    </select>
                    <button class="btn btn-info" onclick="toggleBulkActions()"><i class="fas fa-tasks"></i> Bulk Actions</button>
                </div>
                
                <div id="bulk-actions" class="bulk-actions">
                    <h4>Bulk Actions</h4>
                    <div id="selected-count">0 submissions selected</div>
                    <div class="submission-actions">
                        <button class="btn btn-success" onclick="bulkUpdate('read')"><i class="fas fa-eye"></i> Mark as Read</button>
                        <button class="btn btn-warning" onclick="bulkUpdate('replied')"><i class="fas fa-reply"></i> Mark as Replied</button>
                        <button class="btn btn-info" onclick="bulkUpdate('archived')"><i class="fas fa-archive"></i> Archive</button>
                        <button class="btn btn-danger" onclick="bulkDelete()"><i class="fas fa-trash"></i> Delete</button>
                    </div>
                </div>
                
                <div id="submissions">
                    <div class="loading">Loading submissions...</div>
                </div>
            </div>
            
            <div id="tab-analytics" class="tab-content">
                <div class="chart-container">
                    <h3><i class="fas fa-chart-bar"></i> Advanced Analytics</h3>
                    <div id="advanced-analytics">
                        <div class="loading">Loading advanced analytics...</div>
                    </div>
                </div>
            </div>
            
            <div id="tab-system" class="tab-content">
                <div class="system-status">
                    <h3><i class="fas fa-cogs"></i> System Information</h3>
                    <div id="system-logs">
                        <div class="loading">Loading system logs...</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const BACKEND_URL = window.location.origin;
        let selectedSubmissions = new Set();
        let trendsChart = null;
        let statusChart = null;
        
        function showAlert(message, type = 'success') {
            const alertContainer = document.getElementById('alert-container');
            const alertId = 'alert-' + Date.now();
            alertContainer.innerHTML = `
                <div id="${alertId}" class="alert alert-${type}">
                    <i class="fas fa-${type === 'success' ? 'check' : 'exclamation-triangle'}"></i>
                    ${message}
                    <button onclick="document.getElementById('${alertId}').remove()" 
                            style="float: right; background: none; border: none; cursor: pointer;">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
            
            setTimeout(() => {
                const alert = document.getElementById(alertId);
                if (alert) alert.remove();
            }, 5000);
        }
        
        function switchTab(tabName) {
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(`tab-${tabName}`).classList.add('active');
            event.target.classList.add('active');
            
            // Load tab-specific data
            if (tabName === 'analytics') {
                loadAdvancedAnalytics();
            } else if (tabName === 'system') {
                loadSystemLogs();
            }
        }
        
        async function loadDashboard() {
            try {
                // Load basic analytics
                const analyticsResponse = await fetch(BACKEND_URL + '/api/analytics');
                if (!analyticsResponse.ok) throw new Error('Analytics API failed');
                const analytics = await analyticsResponse.json();
                
                if (analytics.success) {
                    document.getElementById('stats').innerHTML = `
                        <div class="stat-card">
                            <div class="stat-number">${analytics.data.submissions.total}</div>
                            <div>Total Submissions</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${analytics.data.submissions.today}</div>
                            <div>Today</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${analytics.data.submissions.unique_emails}</div>
                            <div>Unique Emails</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${analytics.data.submissions.this_week}</div>
                            <div>This Week</div>
                        </div>
                    `;
                    
                    // Load charts
                    loadCharts(analytics.data);
                }
                
                // Load submissions for submissions tab
                loadSubmissions();
                
            } catch (error) {
                console.error('Dashboard error:', error);
                showAlert('Error loading dashboard: ' + error.message, 'error');
            }
        }
        
        function loadCharts(data) {
            // Trends Chart
            const trendsCtx = document.getElementById('trendsChart').getContext('2d');
            if (trendsChart) trendsChart.destroy();
            
            trendsChart = new Chart(trendsCtx, {
                type: 'line',
                data: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    datasets: [{
                        label: 'Submissions',
                        data: [12, 19, 8, 15, 12, 18, 14],
                        borderColor: '#f43f5e',
                        backgroundColor: '
