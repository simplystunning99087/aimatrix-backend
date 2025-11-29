from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os
from typing import List

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./aimatrix.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Model
class ContactSubmission(Base):
    __tablename__ = "contact_submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, index=True)
    message = Column(Text)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String)

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ContactForm(BaseModel):
    name: str
    email: str
    message: str

class PredictInput(BaseModel):
    text: str

app = FastAPI(title="AIMatrix Backend API", version="1.0.0")

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
        "version": "1.0.0",
        "database": "connected"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/contact")
async def submit_contact(form: ContactForm, request: Request, db: Session = Depends(get_db)):
    try:
        # Get client IP
        client_ip = request.client.host
        
        # Save to database
        db_contact = ContactSubmission(
            name=form.name,
            email=form.email,
            message=form.message,
            ip_address=client_ip
        )
        db.add(db_contact)
        db.commit()
        db.refresh(db_contact)
        
        print(f"📧 New contact saved to database (ID: {db_contact.id})")
        
        return {
            "success": True,
            "message": "Thank you for your message! We'll get back to you within 24 hours.",
            "submission_id": db_contact.id,
            "submitted_data": {
                "name": form.name,
                "email": form.email,
                "message_length": len(form.message)
            }
        }
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# NEW: Get all submissions (protected - for admin later)
@app.get("/api/submissions")
def get_submissions(db: Session = Depends(get_db)):
    submissions = db.query(ContactSubmission).order_by(ContactSubmission.submitted_at.desc()).all()
    return {
        "count": len(submissions),
        "submissions": [
            {
                "id": sub.id,
                "name": sub.name,
                "email": sub.email,
                "message": sub.message,
                "submitted_at": sub.submitted_at.isoformat(),
                "ip_address": sub.ip_address
            }
            for sub in submissions
        ]
    }

# NEW: Analytics endpoint
@app.get("/api/analytics")
def get_analytics(db: Session = Depends(get_db)):
    total_submissions = db.query(ContactSubmission).count()
    today = datetime.utcnow().date()
    today_submissions = db.query(ContactSubmission).filter(
        ContactSubmission.submitted_at >= today
    ).count()
    
    return {
        "total_submissions": total_submissions,
        "today_submissions": today_submissions,
        "unique_emails": db.query(ContactSubmission.email).distinct().count()
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
