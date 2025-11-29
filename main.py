from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from datetime import datetime
from typing import List

# Simple in-memory storage
submissions = []
next_id = 1

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

@app.get("/")
def root():
    return {
        "status": "running", 
        "service": "AIMatrix Backend API",
        "version": "2.0.0",
        "storage": "memory"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/contact")
async def submit_contact(form: ContactForm, request: Request):
    global next_id
    try:
        # Get client IP
        client_ip = request.client.host
        
        # Save to memory
        submission = {
            "id": next_id,
            "name": form.name,
            "email": form.email,
            "message": form.message,
            "submitted_at": datetime.utcnow().isoformat(),
            "ip_address": client_ip
        }
        
        submissions.append(submission)
        next_id += 1
        
        print(f"📧 New contact saved (ID: {submission['id']})")
        
        return {
            "success": True,
            "message": "Thank you for your message! We'll get back to you within 24 hours.",
            "submission_id": submission["id"],
            "submitted_data": {
                "name": form.name,
                "email": form.email,
                "message_length": len(form.message)
            }
        }
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Get all submissions
@app.get("/api/submissions")
def get_submissions():
    return {
        "count": len(submissions),
        "submissions": submissions[::-1]  # Reverse to show newest first
    }

# Analytics endpoint
@app.get("/api/analytics")
def get_analytics():
    today = datetime.utcnow().date().isoformat()
    today_submissions = len([s for s in submissions if s["submitted_at"].startswith(today)])
    unique_emails = len(set(s["email"] for s in submissions))
    
    return {
        "total_submissions": len(submissions),
        "today_submissions": today_submissions,
        "unique_emails": unique_emails
    }

# Health check with submissions count
@app.get("/api/health/detailed")
def detailed_health_check():
    return {
        "status": "healthy",
        "database": "memory",
        "submissions_count": len(submissions),
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
