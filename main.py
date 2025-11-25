from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import Optional

class ContactForm(BaseModel):
    name: str
    email: str
    message: str

class PredictInput(BaseModel):
    text: str

app = FastAPI(title="AIMatrix Backend API", version="1.0.0")

# CORS - Allow all origins for now
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins temporarily
    allow_credentials=True,
    allow_methods=["*"],
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
    return {"status": "healthy"}

# ✅ FIXED: This endpoint was missing or misconfigured
@app.post("/api/contact")
async def submit_contact(form: ContactForm):
    try:
        print(f"📧 New contact form submission:")
        print(f"Name: {form.name}")
        print(f"Email: {form.email}")
        print(f"Message: {form.message}")
        
        # In production, you would:
        # 1. Save to database
        # 2. Send email notification
        # 3. Log to your system
        
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
        print(f"❌ Contact form error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/predict")
def predict(input: PredictInput):
    # Your ML prediction logic
    score = len(input.text) / 100
    return {
        "input": input.text, 
        "score": round(score, 3),
        "interpretation": "positive" if score > 0.5 else "neutral"
    }

# For Render deployment
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
