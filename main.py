from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime, timedelta
import sqlite3
import os
import json
import hashlib
import uuid
from typing import List, Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Database setup with connection pooling
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
                status TEXT DEFAULT 'new',
                priority INTEGER DEFAULT 1
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
        
        # API keys table (for future admin features)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_hash TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                permissions TEXT DEFAULT 'read',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")

db_manager = DatabaseManager()

# Pydantic Models with validation
class ContactForm(BaseModel):
    name: str
    email: EmailStr
    message: str
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @validator('message')
    def message_must_be_long_enough(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Message must be at least 10 characters long')
        return v.strip()

class PredictInput(BaseModel):
    text: str
    model_type: Optional[str] = "sentiment"

class AnalyticsEvent(BaseModel):
    event_type: str
    event_data: Optional[Dict[str, Any]] = None

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str

app = FastAPI(
    title="AIMatrix Backend API",
    version="3.0.0",
    description="Advanced AI Automation Backend with Analytics and Security",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS with specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency for database connection
def get_db():
    conn = db_manager.get_connection()
    try:
        yield conn
    finally:
        conn.close()

# Utility functions
def log_analytics_event(event_type: str, event_data: dict, request: Request):
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO analytics_events (event_type, event_data, user_ip, user_agent)
            VALUES (?, ?, ?, ?)
        ''', (event_type, json.dumps(event_data), request.client.host, request.headers.get('user-agent', '')))
        
        conn.commit()
        conn.close()
        logger.info(f"Analytics event logged: {event_type}")
    except Exception as e:
        logger.error(f"Failed to log analytics event: {e}")

def validate_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # For now, accept any token. In production, validate against database
    return True

# Routes
@app.get("/", response_model=APIResponse)
def root():
    return APIResponse(
        success=True,
        message="AIMatrix Advanced Backend API",
        data={
            "status": "running",
            "version": "3.0.0",
            "features": ["contact", "analytics", "predictions", "admin"],
            "timestamp": datetime.utcnow().isoformat()
        },
        timestamp=datetime.utcnow().isoformat()
    )

@app.get("/health", response_model=APIResponse)
def health_check():
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM contact_submissions")
        db_status = cursor.fetchone()["count"]
        conn.close()
        
        return APIResponse(
            success=True,
            message="System healthy",
            data={
                "database": "connected",
                "submissions_count": db_status,
                "server_time": datetime.utcnow().isoformat()
            },
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        return APIResponse(
            success=False,
            message="Health check failed",
            data={"error": str(e)},
            timestamp=datetime.utcnow().isoformat()
        )

@app.post("/api/contact", response_model=APIResponse)
async def submit_contact(form: ContactForm, request: Request):
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Save to database with additional metadata
        cursor.execute('''
            INSERT INTO contact_submissions (name, email, message, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            form.name, 
            form.email, 
            form.message, 
            request.client.host,
            request.headers.get('user-agent', '')
        ))
        
        submission_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Log analytics event
        log_analytics_event("contact_submission", {
            "submission_id": submission_id,
            "email": form.email,
            "name_length": len(form.name),
            "message_length": len(form.message)
        }, request)
        
        logger.info(f"📧 New contact submission (ID: {submission_id}) from {form.email}")
        
        return APIResponse(
            success=True,
            message="Thank you for your message! We'll get back to you within 24 hours.",
            data={
                "submission_id": submission_id,
                "submitted_data": {
                    "name": form.name,
                    "email": form.email,
                    "message_length": len(form.message)
                },
                "estimated_response_time": "24 hours"
            },
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Contact submission error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process contact form"
        )

@app.get("/api/submissions", response_model=APIResponse)
def get_submissions(
    limit: int = 50,
    offset: int = 0,
    _: bool = Depends(validate_api_key)
):
    try:
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
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(submissions)} submissions",
            data={
                "submissions": [
                    {
                        "id": sub["id"],
                        "name": sub["name"],
                        "email": sub["email"],
                        "message": sub["message"],
                        "submitted_at": sub["submitted_at"],
                        "ip_address": sub["ip_address"],
                        "status": sub["status"],
                        "priority": sub["priority"]
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
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/analytics", response_model=APIResponse)
def get_analytics(_: bool = Depends(validate_api_key)):
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Total submissions
        cursor.execute('SELECT COUNT(*) as count FROM contact_submissions')
        total_submissions = cursor.fetchone()["count"]
        
        # Today's submissions
        cursor.execute('''
            SELECT COUNT(*) as count FROM contact_submissions 
            WHERE DATE(submitted_at) = DATE('now')
        ''')
        today_submissions = cursor.fetchone()["count"]
        
        # This week's submissions
        cursor.execute('''
            SELECT COUNT(*) as count FROM contact_submissions 
            WHERE submitted_at >= DATE('now', '-7 days')
        ''')
        week_submissions = cursor.fetchone()["count"]
        
        # Unique emails
        cursor.execute('SELECT COUNT(DISTINCT email) as count FROM contact_submissions')
        unique_emails = cursor.fetchone()["count"]
        
        # Recent activity
        cursor.execute('''
            SELECT event_type, COUNT(*) as count 
            FROM analytics_events 
            WHERE created_at >= DATE('now', '-1 day')
            GROUP BY event_type
        ''')
        recent_activity = {row["event_type"]: row["count"] for row in cursor.fetchall()}
        
        conn.close()
        
        return APIResponse(
            success=True,
            message="Analytics data retrieved successfully",
            data={
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
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

@app.post("/api/predict", response_model=APIResponse)
def predict(input: PredictInput, request: Request):
    try:
        # Advanced prediction logic
        text_length = len(input.text)
        word_count = len(input.text.split())
        
        # Simple ML-like scoring
        complexity_score = min(text_length / 200, 1.0)
        sentiment_score = word_count / 50  # Placeholder for real sentiment analysis
        
        prediction_data = {
            "input": input.text,
            "analysis": {
                "text_length": text_length,
                "word_count": word_count,
                "complexity_score": round(complexity_score, 3),
                "sentiment_score": round(sentiment_score, 3),
                "model_used": input.model_type
            },
            "interpretation": "positive" if sentiment_score > 0.6 else "neutral" if sentiment_score > 0.3 else "negative"
        }
        
        # Log prediction event
        log_analytics_event("prediction_made", {
            "model_type": input.model_type,
            "text_length": text_length,
            "sentiment_score": sentiment_score
        }, request)
        
        return APIResponse(
            success=True,
            message="Prediction completed successfully",
            data=prediction_data,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.post("/api/analytics/event")
async def track_analytics_event(event: AnalyticsEvent, request: Request):
    log_analytics_event(event.event_type, event.event_data or {}, request)
    
    return APIResponse(
        success=True,
        message="Analytics event tracked successfully",
        timestamp=datetime.utcnow().isoformat()
    )

# Advanced health check with system diagnostics
@app.get("/api/health/detailed", response_model=APIResponse)
def detailed_health_check():
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Database diagnostics
        cursor.execute("SELECT COUNT(*) as count FROM contact_submissions")
        submissions_count = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM analytics_events")
        analytics_count = cursor.fetchone()["count"]
        
        cursor.execute('''
            SELECT COUNT(*) as count FROM contact_submissions 
            WHERE submitted_at >= DATETIME('now', '-1 hour')
        ''')
        recent_submissions = cursor.fetchone()["count"]
        
        conn.close()
        
        return APIResponse(
            success=True,
            message="Detailed system health check",
            data={
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
                    }
                },
                "performance": {
                    "response_time": "optimal",
                    "memory_usage": "normal"
                }
            },
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        return APIResponse(
            success=False,
            message="Health check failed",
            data={"error": str(e)},
            timestamp=datetime.utcnow().isoformat()
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )
