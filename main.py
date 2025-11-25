from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContactForm(BaseModel):
    name: str
    email: str
    message: str

class PredictInput(BaseModel):
    text: str

app = FastAPI(title="AIMatrix Backend API", version="1.0.0")

# CORS - Allow your Netlify domain and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-netlify-app.netlify.app",  # ← UPDATE WITH YOUR ACTUAL NETLIFY URL
        "https://*.netlify.app",                 # Wildcard for all Netlify subdomains
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "status": "running", 
        "service": "AIMatrix Backend API",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy", 
        "timestamp": "2024-11-25T15:30:00Z"
    }

@app.post("/api/contact")
async def submit_contact(form: ContactForm):
    try:
        # Log the submission
        logger.info(f"📧 New contact submission from: {form.name} ({form.email})")
        
        # In production, you would:
        # 1. Save to database
        # 2. Send email notification
        # 3. Integrate with CRM
        
        return {
            "success": True,
            "message": "Thank you for your message! We'll get back to you within 24 hours.",
            "submitted_data": {
                "name": form.name,
                "email": form.email,
                "message_length": len(form.message)
            }
        }
    except Exception as e:
        logger.error(f"Contact form error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/predict")
def predict(input: PredictInput):
    try:
        # Your ML prediction logic
        score = len(input.text) / 100
        
        logger.info(f"🤖 Prediction request: {len(input.text)} chars")
        
        return {
            "input": input.text, 
            "score": round(score, 3),
            "interpretation": "positive" if score > 0.5 else "neutral"
        }
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail="Prediction failed")

# For Render deployment
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )
