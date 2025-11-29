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
import platform
import psutil

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# ==================== CONFIGURATION ====================
APP_NAME = "AIMatrix Backend"
VERSION = "2.0.0"
MAX_SUBMISSIONS_PER_MINUTE = 10

# ==================== DATABASE SETUP ====================
def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect('contact_submissions.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Contact submissions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            ip_address TEXT,
            status TEXT DEFAULT 'new',
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Performance logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT,
            response_time REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# ==================== PERFORMANCE TRACKING ====================
def track_performance(f):
    """Decorator to track API performance"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        result = f(*args, **kwargs)
        end_time = time.time()
        response_time = end_time - start_time
        
        # Log performance to database
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO performance_logs (endpoint, response_time) VALUES (?, ?)',
                (f.__name__, response_time)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Performance logging error: {e}")
        
        print(f"⏱️ {f.__name__} took {response_time:.2f} seconds")
        return result
    return decorated_function

# ==================== SECURITY & VALIDATION ====================
def get_client_ip():
    """Get client IP address safely"""
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    else:
        ip = request.remote_addr
    return ip

def is_valid_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def sanitize_input(text, max_length=1000):
    """Sanitize user input"""
    if not text:
        return ""
    return ' '.join(text.split())[:max_length]

# ==================== EMAIL NOTIFICATIONS ====================
def send_production_email(submission_data):
    """Send email using a real email service"""
    try:
        # Check if email service is configured
        SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
        SENDGRID_FROM_EMAIL = os.environ.get('SENDGRID_FROM_EMAIL')
        ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@aimatrix.com')
        
        if not all([SENDGRID_API_KEY, SENDGRID_FROM_EMAIL]):
            # Fallback to console logging
            print("📧 EMAIL NOTIFICATION (Configure SENDGRID_API_KEY and SENDGRID_FROM_EMAIL environment variables):")
            print(f"New submission from: {submission_data['name']} ({submission_data['email']})")
            print(f"Message: {submission_data['message'][:100]}...")
            return True
        
        # SendGrid integration
        email_data = {
            "personalizations": [{
                "to": [{"email": ADMIN_EMAIL}],
                "subject": f"🎯 New Contact: {submission_data['name']}"
            }],
            "from": {"email": SENDGRID_FROM_EMAIL},
            "content": [{
                "type": "text/plain",
                "value": f"""
New contact form submission:

Name: {submission_data['name']}
Email: {submission_data['email']}
Message: {submission_data['message']}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
IP: {submission_data.get('ip_address', 'N/A')}

View in admin: https://aimatrix-backend-6t9i.onrender.com/admin
"""
            }]
        }
        
        response = requests.post(
            'https://api.sendgrid.com/v3/mail/send',
            headers={'Authorization': f'Bearer {SENDGRID_API_KEY}', 'Content-Type': 'application/json'},
            json=email_data
        )
        
        if response.status_code == 202:
            print("✅ Email sent successfully via SendGrid")
            return True
        else:
            print(f"❌ Email failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Email error: {e}")
        return False

# ==================== BASIC ENDPOINTS ====================
@app.route('/health')
@track_performance
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM contact_submissions')
        total_submissions = cursor.fetchone()['count']
        
        # Get performance stats
        cursor.execute('''
            SELECT AVG(response_time) as avg_response, MAX(response_time) as max_response
            FROM performance_logs 
            WHERE timestamp >= datetime("now", "-1 hour")
        ''')
        perf_stats = cursor.fetchone()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Service is healthy",
            "data": {
                "app": APP_NAME,
                "version": VERSION,
                "status": "operational",
                "total_submissions": total_submissions,
                "performance": {
                    "avg_response_time": round(perf_stats['avg_response'] or 0, 3),
                    "max_response_time": round(perf_stats['max_response'] or 0, 3)
                },
                "timestamp": datetime.now().isoformat()
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/')
@track_performance
def home():
    """Root endpoint with API documentation"""
    return jsonify({
        "success": True,
        "message": f"{APP_NAME} is running",
        "version": VERSION,
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "GET": [
                "/", "/health", "/api/analytics", "/api/submissions", 
                "/api/analytics/detailed", "/admin", "/api/submissions/export/csv",
                "/api/status", "/api/docs"
            ],
            "POST": ["/api/contact", "/admin/backup"],
            "DELETE": ["/api/submissions/<id>"],
            "PUT": ["/api/submissions/<id>/status", "/api/submissions/<id>/archive"]
        }
    })

@app.route('/api/docs')
@track_performance
def api_documentation():
    """API Documentation"""
    return jsonify({
        "success": True,
        "message": "AIMatrix API Documentation",
        "version": VERSION,
        "endpoints": {
            "GET": {
                "/health": "Service health check with performance metrics",
                "/api/analytics": "Basic analytics data",
                "/api/analytics/detailed": "Detailed analytics with charts data",
                "/api/submissions": "Get all submissions (supports status filter)",
                "/api/status": "System status and monitoring",
                "/api/submissions/export/csv": "Export submissions as CSV",
                "/api/docs": "This documentation"
            },
            "POST": {
                "/api/contact": "Submit contact form (requires: name, email, message)",
                "/admin/backup": "Create database backup"
            },
            "PUT": {
                "/api/submissions/<id>/status": "Update submission status"
            },
            "DELETE": {
                "/api/submissions/<id>": "Delete a specific submission"
            }
        },
        "examples": {
            "contact_submission": {
                "method": "POST",
                "url": "/api/contact",
                "body": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "message": "Hello, I'm interested in your services!"
                }
            },
            "update_status": {
                "method": "PUT", 
                "url": "/api/submissions/1/status",
                "body": {
                    "status": "read"
                }
            }
        }
    })

@app.route('/api/status')
@track_performance
def system_status():
    """Comprehensive system status endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Database info
        cursor.execute('SELECT COUNT(*) as total FROM contact_submissions')
        total_submissions = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as today FROM contact_submissions WHERE DATE(submitted_at) = DATE("now")')
        today_submissions = cursor.fetchone()['today']
        
        # Performance metrics
        cursor.execute('''
            SELECT 
                endpoint,
                AVG(response_time) as avg_response,
                COUNT(*) as calls
            FROM performance_logs 
            WHERE timestamp >= datetime("now", "-1 hour")
            GROUP BY endpoint
        ''')
        performance_data = cursor.fetchall()
        
        conn.close()
        
        # System info (basic)
        system_info = {
            "python_version": platform.python_version(),
            "platform": platform.system(),
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify({
            "success": True,
            "data": {
                "submissions": {
                    "total": total_submissions,
                    "today": today_submissions
                },
                "performance": [dict(row) for row in performance_data],
                "system": system_info
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== CONTACT FORM ENDPOINT ====================
@app.route('/api/contact', methods=['POST', 'GET'])
@track_performance
def contact_submit():
    """Contact form submission with rate limiting and validation"""
    if request.method == 'GET':
        return jsonify({
            "success": True,
            "message": "Contact endpoint is working. Use POST to submit data.",
            "required_fields": ["name", "email", "message"]
        })
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({
                "success": False,
                "error": "No data received"
            }), 400
            
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        message = data.get('message', '').strip()
        
        if not name:
            return jsonify({
                "success": False,
                "error": "Missing required field: name"
            }), 400
            
        if not email:
            return jsonify({
                "success": False,
                "error": "Missing required field: email"
            }), 400
            
        if not is_valid_email(email):
            return jsonify({
                "success": False,
                "error": "Invalid email format"
            }), 400
            
        if not message:
            return jsonify({
                "success": False,
                "error": "Missing required field: message"
            }), 400
        
        # Sanitize inputs
        name = sanitize_input(name, 100)
        email = sanitize_input(email, 100)
        message = sanitize_input(message, 2000)
        
        # Get client IP address
        ip_address = get_client_ip()
        
        # Check rate limiting
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as recent_count FROM contact_submissions 
            WHERE ip_address = ? AND submitted_at >= datetime('now', '-1 minute')
        ''', (ip_address,))
        recent_count = cursor.fetchone()['recent_count']
        
        if recent_count >= MAX_SUBMISSIONS_PER_MINUTE:
            conn.close()
            return jsonify({
                "success": False,
                "error": "Too many submissions. Please try again in a minute."
            }), 429
        
        # Insert into database
        cursor.execute('''
            INSERT INTO contact_submissions (name, email, message, ip_address)
            VALUES (?, ?, ?, ?)
        ''', (name, email, message, ip_address))
        conn.commit()
        
        # Get the inserted ID
        submission_id = cursor.lastrowid
        conn.close()
        
        print(f"✅ Contact form submitted successfully (ID: {submission_id})")
        
        # Send email notification
        send_production_email({
            'name': name,
            'email': email,
            'message': message,
            'ip_address': ip_address
        })
        
        return jsonify({
            "success": True,
            "message": "Contact form submitted successfully",
            "submission_id": submission_id,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print("❌ Contact form error:", str(e))
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ==================== SUBMISSIONS MANAGEMENT ====================
@app.route('/api/submissions', methods=['GET'])
@track_performance
def get_submissions():
    """Get all submissions with pagination"""
    try:
        status_filter = request.args.get('status', 'all')
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT id, name, email, message, ip_address, status, submitted_at
            FROM contact_submissions 
            WHERE 1=1
        '''
        params = []
        
        if status_filter != 'all':
            query += ' AND status = ?'
            params.append(status_filter)
            
        query += ' ORDER BY submitted_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        submissions = cursor.fetchall()
        
        # Get total count for pagination
        count_query = 'SELECT COUNT(*) as total FROM contact_submissions WHERE 1=1'
        count_params = []
        
        if status_filter != 'all':
            count_query += ' AND status = ?'
            count_params.append(status_filter)
            
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()['total']
        
        conn.close()
        
        submissions_list = [dict(row) for row in submissions]
        
        return jsonify({
            "success": True,
            "message": f"Retrieved {len(submissions_list)} submissions",
            "data": {
                "submissions": submissions_list,
                "pagination": {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                    "has_more": (offset + limit) < total
                }
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/submissions/<int:submission_id>', methods=['DELETE'])
@track_performance
def delete_submission(submission_id):
    """Delete a specific submission"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First check if submission exists
        cursor.execute('SELECT id FROM contact_submissions WHERE id = ?', (submission_id,))
        submission = cursor.fetchone()
        
        if not submission:
            conn.close()
            return jsonify({
                'success': False,
                'error': f'Submission {submission_id} not found'
            }), 404
        
        # Delete the submission
        cursor.execute('DELETE FROM contact_submissions WHERE id = ?', (submission_id,))
        conn.commit()
        conn.close()
        
        print(f"✅ Submission {submission_id} deleted successfully")
        
        return jsonify({
            'success': True,
            'message': f'Submission {submission_id} deleted successfully'
        })
        
    except Exception as e:
        print(f"❌ Delete submission error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/submissions/<int:submission_id>/status', methods=['PUT'])
@track_performance
def update_submission_status(submission_id):
    """Update submission status"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({
                'success': False,
                'error': 'Status field is required'
            }), 400
        
        valid_statuses = ['new', 'read', 'archived', 'replied']
        if new_status not in valid_statuses:
            return jsonify({
                'success': False,
                'error': f'Invalid status. Must be one of: {valid_statuses}'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First check if submission exists
        cursor.execute('SELECT id FROM contact_submissions WHERE id = ?', (submission_id,))
        submission = cursor.fetchone()
        
        if not submission:
            conn.close()
            return jsonify({
                'success': False,
                'error': f'Submission {submission_id} not found'
            }), 404
        
        # Update the status
        cursor.execute(
            'UPDATE contact_submissions SET status = ? WHERE id = ?',
            (new_status, submission_id)
        )
        conn.commit()
        conn.close()
        
        print(f"✅ Submission {submission_id} status updated to {new_status}")
        
        return jsonify({
            'success': True,
            'message': f'Submission {submission_id} status updated to {new_status}'
        })
        
    except Exception as e:
        print(f"❌ Update status error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/submissions/<int:submission_id>/archive', methods=['POST'])
@track_performance
def archive_submission(submission_id):
    """Archive a submission"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First check if submission exists
        cursor.execute('SELECT id FROM contact_submissions WHERE id = ?', (submission_id,))
        submission = cursor.fetchone()
        
        if not submission:
            conn.close()
            return jsonify({
                'success': False,
                'error': f'Submission {submission_id} not found'
            }), 404
        
        cursor.execute(
            'UPDATE contact_submissions SET status = "archived" WHERE id = ?',
            (submission_id,)
        )
        conn.commit()
        conn.close()
        
        print(f"✅ Submission {submission_id} archived successfully")
        
        return jsonify({
            'success': True,
            'message': f'Submission {submission_id} archived successfully'
        })
    except Exception as e:
        print(f"❌ Archive submission error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== ANALYTICS ENDPOINTS ====================
@app.route('/api/analytics', methods=['GET'])
@track_performance
def analytics():
    """Basic analytics data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total submissions
        cursor.execute('SELECT COUNT(*) as total FROM contact_submissions')
        total = cursor.fetchone()['total']
        
        # Today's submissions
        cursor.execute('''
            SELECT COUNT(*) as today FROM contact_submissions 
            WHERE DATE(submitted_at) = DATE('now')
        ''')
        today = cursor.fetchone()['today']
        
        # This week's submissions
        cursor.execute('''
            SELECT COUNT(*) as this_week FROM contact_submissions 
            WHERE submitted_at >= DATE('now', '-7 days')
        ''')
        this_week = cursor.fetchone()['this_week']
        
        # Unique emails
        cursor.execute('SELECT COUNT(DISTINCT email) as unique_emails FROM contact_submissions')
        unique_emails = cursor.fetchone()['unique_emails']
        
        # Status distribution
        cursor.execute('''
            SELECT status, COUNT(*) as count 
            FROM contact_submissions 
            GROUP BY status
        ''')
        status_data = cursor.fetchall()
        status_distribution = {row['status']: row['count'] for row in status_data}
        
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Analytics data retrieved successfully",
            "data": {
                "submissions": {
                    "total": total,
                    "today": today,
                    "this_week": this_week,
                    "unique_emails": unique_emails
                },
                "status_distribution": status_distribution
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/analytics/detailed', methods=['GET'])
@track_performance
def detailed_analytics():
    """Detailed analytics for charts and advanced reporting"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Last 7 days daily submissions
        cursor.execute('''
            SELECT DATE(submitted_at) as date, COUNT(*) as count 
            FROM contact_submissions 
            WHERE submitted_at >= DATE('now', '-7 days')
            GROUP BY DATE(submitted_at) 
            ORDER BY date
        ''')
        daily_data = cursor.fetchall()
        
        # Hourly distribution (last 24 hours)
        cursor.execute('''
            SELECT strftime('%H', submitted_at) as hour, COUNT(*) as count
            FROM contact_submissions 
            WHERE submitted_at >= datetime('now', '-1 day')
            GROUP BY hour 
            ORDER BY hour
        ''')
        hourly_data = cursor.fetchall()
        
        # Top submitters
        cursor.execute('''
            SELECT email, COUNT(*) as submission_count
            FROM contact_submissions 
            GROUP BY email 
            ORDER BY submission_count DESC 
            LIMIT 10
        ''')
        top_submitters = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'daily_submissions': [dict(row) for row in daily_data],
                'hourly_distribution': [dict(row) for row in hourly_data],
                'top_submitters': [dict(row) for row in top_submitters]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== EXPORT FUNCTIONALITY ====================
@app.route('/api/submissions/export/csv', methods=['GET'])
@track_performance
def export_submissions_csv():
    """Export all submissions as CSV"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, email, message, ip_address, status, submitted_at 
            FROM contact_submissions 
            ORDER BY submitted_at DESC
        ''')
        submissions = cursor.fetchall()
        conn.close()
        
        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['ID', 'Name', 'Email', 'Message', 'IP Address', 'Status', 'Submitted At'])
        
        # Write data
        for sub in submissions:
            writer.writerow([
                sub['id'],
                sub['name'],
                sub['email'],
                sub['message'],
                sub['ip_address'],
                sub['status'],
                sub['submitted_at']
            ])
        
        # Prepare response
        output.seek(0)
        return output.getvalue(), 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment;filename=aimatrix_submissions.csv'
        }
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== BACKUP FUNCTIONALITY ====================
@app.route('/admin/backup', methods=['POST'])
@track_performance
def create_backup():
    """Create database backup"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'backup_{timestamp}.db'
        shutil.copy2('contact_submissions.db', backup_file)
        
        # Get backup size
        backup_size = os.path.getsize(backup_file)
        
        return jsonify({
            'success': True, 
            'message': 'Backup created successfully',
            'backup_file': backup_file,
            'backup_size': backup_size,
            'timestamp': timestamp
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== ADMIN DASHBOARD ====================
@app.route('/admin')
def serve_admin():
    """Serve the admin dashboard"""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard - AIMatrix</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
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
        
        .btn-primary {
            background: var(--primary);
            color: white;
        }
        
        .btn-success {
            background: var(--success);
            color: white;
        }
        
        .btn-danger {
            background: var(--danger);
            color: white;
        }
        
        .btn-warning {
            background: var(--warning);
            color: white;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
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
        
        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .status-new { background: #dbeafe; color: #1e40af; }
        .status-read { background: #dcfce7; color: #166534; }
        .status-archived { background: #f3f4f6; color: #374151; }
        .status-replied { background: #fef3c7; color: #92400e; }
        
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
        
        .alert-success {
            background: #dcfce7;
            color: #166534;
            border: 1px solid #bbf7d0;
        }
        
        .alert-error {
            background: #fee2e2;
            color: #991b1b;
            border: 1px solid #fecaca;
        }
        
        .system-status {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .status-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #f1f5f9;
        }
        
        @media (max-width: 768px) {
            .header {
                flex-direction: column;
                align-items: flex-start;
            }
            
            .stats {
                grid-template-columns: 1fr 1fr;
            }
            
            .submission-actions {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 AIMatrix Admin Dashboard v2.0</h1>
            <div class="controls">
                <button class="btn btn-primary" onclick="loadDashboard()">🔄 Refresh</button>
                <button class="btn btn-success" onclick="exportData()">📤 Export CSV</button>
                <button class="btn btn-warning" onclick="createBackup()">💾 Backup</button>
                <button class="btn btn-primary" onclick="showSystemStatus()">📊 System Status</button>
            </div>
        </div>
        
        <div id="alert-container"></div>
        <div id="system-status" class="system-status" style="display: none;"></div>
        
        <div class="stats" id="stats">
            <div class="loading">Loading analytics...</div>
        </div>
        
        <h2>📨 Contact Form Submissions</h2>
        <div id="submissions">
            <div class="loading">Loading submissions...</div>
        </div>
    </div>

    <script>
        const BACKEND_URL = window.location.origin;
        
        function showAlert(message, type = 'success') {
            const alertContainer = document.getElementById('alert-container');
            const alertId = 'alert-' + Date.now();
            alertContainer.innerHTML = `
                <div id="${alertId}" class="alert alert-${type}">
                    ${message}
                    <button onclick="document.getElementById('${alertId}').remove()" 
                            style="float: right; background: none; border: none; cursor: pointer;">✕</button>
                </div>
            `;
            
            setTimeout(() => {
                const alert = document.getElementById(alertId);
                if (alert) alert.remove();
            }, 5000);
        }
        
        async function loadDashboard() {
            try {
                document.getElementById('stats').innerHTML = '<div class="loading">Loading analytics...</div>';
                document.getElementById('submissions').innerHTML = '<div class="loading">Loading submissions...</div>';
                
                // Load analytics
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
                }
                
                // Load submissions
                const submissionsResponse = await fetch(BACKEND_URL + '/api/submissions');
                if (!submissionsResponse.ok) throw new Error('Submissions API failed');
                const submissionsData = await submissionsResponse.json();
                
                if (submissionsData.success) {
                    const submissions = submissionsData.data.submissions;
                    
                    if (submissions.length === 0) {
                        document.getElementById('submissions').innerHTML = `
                            <div class="empty-state">
                                <h3>No submissions yet</h3>
                                <p>Contact form submissions will appear here.</p>
                            </div>
                        `;
                        return;
                    }
                    
                    document.getElementById('submissions').innerHTML = `
                        <div class="submissions-grid">
                            ${submissions.map(sub => `
                                <div class="submission-card">
                                    <div class="submission-header">
                                        <div>
                                            <strong>${sub.name}</strong> 
                                            <span style="color: var(--muted);">• ${sub.email}</
