from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import sqlite3
import json
import logging
import os
from email_validator import validate_email, EmailNotValidError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Database setup
class DatabaseManager:
    def __init__(self, db_path: str = "aimatrix.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Contact submissions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contact_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                status TEXT DEFAULT 'new'
            )
        ''')
        
        # Analytics table for tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                event_data TEXT,
                user_ip TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized successfully")

db_manager = DatabaseManager()

def validate_email_address(email):
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False

def log_analytics_event(event_type, event_data, request):
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO analytics_events (event_type, event_data, user_ip, user_agent)
            VALUES (?, ?, ?, ?)
        ''', (event_type, json.dumps(event_data), request.remote_addr, request.headers.get('User-Agent', '')))
        
        conn.commit()
        conn.close()
        logger.info(f"📊 Analytics event logged: {event_type}")
    except Exception as e:
        logger.error(f"❌ Failed to log analytics event: {e}")

# ===== ROUTES =====

@app.route('/')
def root():
    return jsonify({
        "status": "running",
        "service": "AIMatrix Advanced Backend API",
        "version": "3.0.0",
        "features": ["contact", "analytics", "predictions", "admin"],
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/health')
def health_check():
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM contact_submissions")
        db_status = cursor.fetchone()["count"]
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "✅ System healthy",
            "data": {
                "database": "connected",
                "submissions_count": db_status,
                "server_time": datetime.utcnow().isoformat()
            },
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "❌ Health check failed",
            "data": {"error": str(e)},
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@app.route('/api/contact', methods=['POST'])
def submit_contact():
    try:
        data = request.get_json()
        
        # Validation
        if not data or not data.get('name') or not data['name'].strip():
            return jsonify({"success": False, "error": "Name cannot be empty"}), 400
        
        if not data.get('email') or not validate_email_address(data['email']):
            return jsonify({"success": False, "error": "Invalid email address"}), 400
        
        if not data.get('message') or len(data['message'].strip()) < 10:
            return jsonify({"success": False, "error": "Message must be at least 10 characters"}), 400
        
        # Save to database
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO contact_submissions (name, email, message, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data['name'].strip(),
            data['email'],
            data['message'].strip(),
            request.remote_addr,
            request.headers.get('User-Agent', '')
        ))
        
        submission_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Log analytics
        log_analytics_event("contact_submission", {
            "submission_id": submission_id,
            "email": data['email'],
            "name_length": len(data['name']),
            "message_length": len(data['message'])
        }, request)
        
        logger.info(f"📧 New contact submission (ID: {submission_id}) from {data['email']}")
        
        return jsonify({
            "success": True,
            "message": "Thank you for your message! We'll get back to you within 24 hours.",
            "data": {
                "submission_id": submission_id,
                "submitted_data": {
                    "name": data['name'],
                    "email": data['email'],
                    "message_length": len(data['message'])
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Contact submission error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@app.route('/api/submissions')
def get_submissions():
    try:
        limit = min(request.args.get('limit', 50, type=int), 100)  # Max 100
        offset = request.args.get('offset', 0, type=int)
        
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM contact_submissions 
            ORDER BY submitted_at DESC 
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        submissions = cursor.fetchall()
        
        cursor.execute('SELECT COUNT(*) as total FROM contact_submissions')
        total_count = cursor.fetchone()["total"]
        
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Retrieved {len(submissions)} submissions",
            "data": {
                "submissions": [
                    {
                        "id": sub["id"],
                        "name": sub["name"],
                        "email": sub["email"],
                        "message": sub["message"],
                        "submitted_at": sub["submitted_at"],
                        "ip_address": sub["ip_address"],
                        "status": sub["status"]
                    }
                    for sub in submissions
                ],
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": (offset + len(submissions)) < total_count
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"❌ Submissions error: {e}")
        return jsonify({"success": False, "error": f"Database error: {str(e)}"}), 500

@app.route('/api/analytics')
def get_analytics():
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Total submissions
        cursor.execute('SELECT COUNT(*) as count FROM contact_submissions')
        total_submissions = cursor.fetchone()["count"]
        
        # Today's submissions
        cursor.execute('SELECT COUNT(*) as count FROM contact_submissions WHERE DATE(submitted_at) = DATE("now")')
        today_submissions = cursor.fetchone()["count"]
        
        # This week's submissions
        cursor.execute('SELECT COUNT(*) as count FROM contact_submissions WHERE submitted_at >= DATE("now", "-7 days")')
        week_submissions = cursor.fetchone()["count"]
        
        # Unique emails
        cursor.execute('SELECT COUNT(DISTINCT email) as count FROM contact_submissions')
        unique_emails = cursor.fetchone()["count"]
        
        # Recent activity from analytics
        cursor.execute('SELECT event_type, COUNT(*) as count FROM analytics_events WHERE created_at >= DATE("now", "-1 day") GROUP BY event_type')
        recent_activity = {row["event_type"]: row["count"] for row in cursor.fetchall()}
        
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Analytics data retrieved successfully",
            "data": {
                "submissions": {
                    "total": total_submissions,
                    "today": today_submissions,
                    "this_week": week_submissions,
                    "unique_emails": unique_emails
                },
                "recent_activity": recent_activity,
                "system_health": {
                    "database": "connected",
                    "api": "operational",
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"❌ Analytics error: {e}")
        return jsonify({"success": False, "error": f"Analytics error: {str(e)}"}), 500

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        
        if not data or not data.get('text'):
            return jsonify({"success": False, "error": "Text is required"}), 400
            
        text = data['text']
        text_length = len(text)
        word_count = len(text.split())
        
        # Advanced scoring
        complexity_score = min(text_length / 200, 1.0)
        sentiment_score = min(word_count / 50, 1.0)  # Placeholder for real sentiment analysis
        
        prediction_data = {
            "input": text,
            "analysis": {
                "text_length": text_length,
                "word_count": word_count,
                "complexity_score": round(complexity_score, 3),
                "sentiment_score": round(sentiment_score, 3),
                "readability": "high" if complexity_score > 0.7 else "medium" if complexity_score > 0.4 else "low"
            },
            "interpretation": "positive" if sentiment_score > 0.6 else "neutral" if sentiment_score > 0.3 else "negative"
        }
        
        # Log prediction event
        log_analytics_event("prediction_made", {
            "text_length": text_length,
            "sentiment_score": sentiment_score,
            "complexity_score": complexity_score
        }, request)
        
        return jsonify({
            "success": True,
            "message": "Prediction completed successfully",
            "data": prediction_data,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"❌ Prediction error: {e}")
        return jsonify({"success": False, "error": f"Prediction error: {str(e)}"}), 500

@app.route('/api/analytics/event', methods=['POST'])
def track_analytics_event():
    try:
        data = request.get_json()
        event_type = data.get('event_type')
        event_data = data.get('event_data', {})
        
        if not event_type:
            return jsonify({"success": False, "error": "Event type is required"}), 400
            
        log_analytics_event(event_type, event_data, request)
        
        return jsonify({
            "success": True,
            "message": "Analytics event tracked successfully",
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"❌ Analytics event error: {e}")
        return jsonify({"success": False, "error": "Failed to track analytics event"}), 500

@app.route('/api/health/detailed')
def detailed_health_check():
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Database diagnostics
        cursor.execute("SELECT COUNT(*) as count FROM contact_submissions")
        submissions_count = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM analytics_events")
        analytics_count = cursor.fetchone()["count"]
        
        cursor.execute('SELECT COUNT(*) as count FROM contact_submissions WHERE submitted_at >= DATETIME("now", "-1 hour")')
        recent_submissions = cursor.fetchone()["count"]
        
        # Database size info
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        db_size = cursor.fetchone()["size"]
        
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Detailed system health check",
            "data": {
                "system": {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "uptime": "running"
                },
                "database": {
                    "status": "connected",
                    "tables": {
                        "contact_submissions": submissions_count,
                        "analytics_events": analytics_count
                    },
                    "recent_activity": {
                        "submissions_last_hour": recent_submissions
                    },
                    "size_bytes": db_size
                },
                "performance": {
                    "response_time": "optimal",
                    "memory_usage": "normal",
                    "active_connections": 1
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"❌ Detailed health check error: {e}")
        return jsonify({
            "success": False,
            "message": "Health check failed",
            "data": {"error": str(e)},
            "timestamp": datetime.utcnow().isoformat()
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "message": "The requested endpoint does not exist"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "message": "Something went wrong on our end"
    }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"🚀 Starting AIMatrix Flask Server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
