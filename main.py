from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

# Database setup
DATABASE_URL = "aimatrix.db"

def init_database():
    """Initialize the SQLite database"""
    conn = sqlite3.connect(DABASE_URL)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

class ContactForm(BaseModel):
    name: str
    email: str
    message: str

class PredictInput(BaseModel):
    text: str

app = FastAPI(title="AIMatrix Backend API", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

@app.get("/")
def root():
    return {
        "status": "running", 
        "service": "AIMatrix Backend API",
        "version": "2.0.0",
        "database": "sqlite"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/contact")
async def submit_contact(form: ContactForm, request: Request):
    try:
        # Get client IP
        client_ip = request.client.host
        
        # Save to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO contact_submissions (name, email, message, ip_address)
            VALUES (?, ?, ?, ?)
        ''', (form.name, form.email, form.message, client_ip))
        
        submission_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"📧 New contact saved to database (ID: {submission_id})")
        
        return {
            "success": True,
            "message": "Thank you for your message! We'll get back to you within 24 hours.",
            "submission_id": submission_id,
            "submitted_data": {
                "name": form.name,
                "email": form.email,
                "message_length": len(form.message)
            }
        }
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# NEW: Get all submissions
@app.get("/api/submissions")
def get_submissions():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM contact_submissions 
            ORDER BY submitted_at DESC
        ''')
        
        submissions = cursor.fetchall()
        conn.close()
        
        return {
            "count": len(submissions),
            "submissions": [
                {
                    "id": sub["id"],
                    "name": sub["name"],
                    "email": sub["email"],
                    "message": sub["message"],
                    "submitted_at": sub["submitted_at"],
                    "ip_address": sub["ip_address"]
                }
                for sub in submissions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# NEW: Analytics endpoint
@app.get("/api/analytics")
def get_analytics():
    try:
        conn = get_db_connection()
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
        
        # Unique emails
        cursor.execute('SELECT COUNT(DISTINCT email) as count FROM contact_submissions')
        unique_emails = cursor.fetchone()["count"]
        
        conn.close()
        
        return {
            "total_submissions": total_submissions,
            "today_submissions": today_submissions,
            "unique_emails": unique_emails
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

# NEW: Health check with database
@app.get("/api/health/detailed")
def detailed_health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if database is accessible
        cursor.execute('SELECT COUNT(*) as count FROM contact_submissions')
        db_count = cursor.fetchone()["count"]
        conn.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "submissions_count": db_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "degraded",
            "database": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.post("/predict")
def predict(input: PredictInput):
    score = len(input.text) / 100
    return {
        "input": input.text, 
        "score": round(score, 3),
        "interpretation": "positive" if score > 0.5 else "neutral"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
