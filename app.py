from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime, timedelta
import csv
from io import StringIO

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database setup
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
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Serve admin.html from the backend
@app.route('/admin')
def serve_admin():
    """Serve the admin dashboard"""
    return """
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
                display: none;
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
                <h1>📊 AIMatrix Admin Dashboard</h1>
                <div class="controls">
                    <button class="btn btn-primary" onclick="loadDashboard()">🔄 Refresh</button>
                    <button class="btn btn-success" onclick="exportData()">📤 Export CSV</button>
                    <button class="btn btn-warning" onclick="clearAllData()">🗑️ Clear All</button>
                </div>
            </div>
            
            <div id="alert-container"></div>
            
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
                        <button onclick="document.getElementById('${alertId}').style.display='none'" 
                                style="float: right; background: none; border: none; cursor: pointer;">✕</button>
                    </div>
                `;
                document.getElementById(alertId).style.display = 'block';
                
                // Auto-hide after 5 seconds
                setTimeout(() => {
                    const alert = document.getElementById(alertId);
                    if (alert) alert.style.display = 'none';
                }, 5000);
            }
            
            async function loadDashboard() {
                try {
                    // Show loading states
                    document.getElementById('stats').innerHTML = '<div class="loading">Loading analytics...</div>';
                    document.getElementById('submissions').innerHTML = '<div class="loading">Loading submissions...</div>';
                    
                    // Load analytics
                    const analyticsResponse = await fetch(`${BACKEND_URL}/api/analytics`);
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
                    const submissionsResponse = await fetch(`${BACKEND_URL}/api/submissions`);
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
                                                <span style="color: var(--muted);">• ${sub.email}</span>
                                                <div class="submission-meta">
                                                    ${new Date(sub.submitted_at).toLocaleString()} • IP: ${sub.ip_address}
                                                </div>
                                            </div>
                                            <span class="status-badge status-${sub.status}">${sub.status}</span>
                                        </div>
                                        <p>${sub.message}</p>
                                        <div class="submission-actions">
                                            <button class="btn btn-success" onclick="markAsRead(${sub.id})">✓ Read</button>
                                            <button class="btn btn-primary" onclick="replyTo('${sub.email}')">📧 Reply</button>
                                            <button class="btn btn-danger" onclick="deleteSubmission(${sub.id})">🗑️ Delete</button>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        `;
                    }
                    
                } catch (error) {
                    console.error('Dashboard error:', error);
                    showAlert('Error loading data. Check console.', 'error');
                }
            }
            
            async function markAsRead(submissionId) {
                try {
                    const response = await fetch(`${BACKEND_URL}/api/submissions/${submissionId}/status`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ status: 'read' })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        showAlert('Submission marked as read');
                        loadDashboard(); // Refresh the dashboard
                    } else {
                        throw new Error(result.error);
                    }
                } catch (error) {
                    showAlert('Error updating status: ' + error.message, 'error');
                }
            }
            
            function replyTo(email) {
                window.open(`mailto:${email}?subject=Re: Your AIMatrix Inquiry`, '_blank');
            }
            
            async function deleteSubmission(submissionId) {
                if (confirm('Are you sure you want to delete this submission?')) {
                    try {
                        const response = await fetch(`${BACKEND_URL}/api/submissions/${submissionId}`, {
                            method: 'DELETE'
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            showAlert('Submission deleted successfully');
                            loadDashboard(); // Refresh the dashboard
                        } else {
                            throw new Error(result.error);
                        }
                    } catch (error) {
                        showAlert('Error deleting submission: ' + error.message, 'error');
                    }
                }
            }
            
            function exportData() {
                window.open(`${BACKEND_URL}/api/submissions/export/csv`, '_blank');
            }
            
            async function clearAllData() {
                if (confirm('⚠️ Are you absolutely sure? This will delete ALL submissions and cannot be undone!')) {
                    try {
                        // Delete all submissions one by one
                        const submissionsResponse = await fetch(`${BACKEND_URL}/api/submissions`);
                        const submissionsData = await submissionsResponse.json();
                        
                        if (submissionsData.success) {
                            const submissions = submissionsData.data.submissions;
                            
                            for (const sub of submissions) {
                                await fetch(`${BACKEND_URL}/api/submissions/${sub.id}`, {
                                    method: 'DELETE'
                                });
                            }
                            
                            showAlert('All submissions cleared successfully');
                            loadDashboard(); // Refresh the dashboard
                        }
                    } catch (error) {
                        showAlert('Error clearing data: ' + error.message, 'error');
                    }
                }
            }
            
            // Load dashboard on page load and every 30 seconds
            document.addEventListener('DOMContentLoaded', loadDashboard);
            setInterval(loadDashboard, 30000);
        </script>
    </body>
    </html>
    """

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({
        "success": True,
        "message": "Service is healthy",
        "timestamp": datetime.now().isoformat()
    })

# Root endpoint
@app.route('/')
def home():
    return jsonify({
        "success": True,
        "message": "AIMatrix Backend API is running",
        "endpoints": {
            "health": "/health",
            "contact": "/api/contact",
            "analytics": "/api/analytics", 
            "submissions": "/api/submissions",
            "admin": "/admin"
        },
        "timestamp": datetime.now().isoformat()
    })

# Contact form submission
@app.route('/api/contact', methods=['POST'])
def contact_submit():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('name') or not data.get('email') or not data.get('message'):
            return jsonify({
                "success": False,
                "error": "Missing required fields: name, email, message"
            }), 400
        
        # Get client IP address
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        
        # Insert into database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO contact_submissions (name, email, message, ip_address)
            VALUES (?, ?, ?, ?)
        ''', (data['name'], data['email'], data['message'], ip_address))
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Contact form submitted successfully",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Get all submissions
@app.route('/api/submissions')
def get_submissions():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, email, message, ip_address, status, submitted_at
            FROM contact_submissions 
            ORDER BY submitted_at DESC
            LIMIT 50
        ''')
        submissions = cursor.fetchall()
        conn.close()
        
        submissions_list = []
        for row in submissions:
            submissions_list.append(dict(row))
        
        return jsonify({
            "success": True,
            "message": f"Retrieved {len(submissions_list)} submissions",
            "data": {
                "submissions": submissions_list,
                "pagination": {
                    "total": len(submissions_list),
                    "limit": 50,
                    "offset": 0,
                    "has_more": False
                }
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Analytics endpoint
@app.route('/api/analytics')
def analytics():
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
                }
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# NEW: Delete submission endpoint
@app.route('/api/submissions/<int:submission_id>', methods=['DELETE'])
def delete_submission(submission_id):
    """Delete a specific submission"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM contact_submissions WHERE id = ?', (submission_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Submission {submission_id} deleted successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# NEW: Export submissions as CSV
@app.route('/api/submissions/export/csv')
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

# NEW: Update submission status
@app.route('/api/submissions/<int:submission_id>/status', methods=['PUT'])
def update_submission_status(submission_id):
    """Update submission status"""
    try:
        data = request.get_json()
        new_status = data.get('status', 'read')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE contact_submissions SET status = ? WHERE id = ?',
            (new_status, submission_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Submission {submission_id} status updated to {new_status}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
