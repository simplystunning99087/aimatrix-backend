# startup-site
🔧 Backend Repository
AIMatrix Backend - API & Admin System
A robust Node.js backend with Express.js, MongoDB, and Resend.com integration for the AIMatrix platform.

✨ Features
RESTful API: Clean, well-structured API endpoints

MongoDB Integration: MongoDB with Mongoose ODM

Email Service: Resend.com integration with HTML templates

Admin Dashboard: Enhanced admin interface with analytics

Contact Management: Form submission handling with email notifications

Real-time Analytics: Submission tracking and statistics

Security: CORS, input validation, and error handling

🛠 Tech Stack
Backend: Node.js, Express.js

Database: MongoDB with Mongoose

Email: Resend.com API

Authentication: (Optional) JWT for admin routes

Documentation: API docs with Swagger/OpenAPI

Deployment: Render.com

📦 Installation & Setup
Clone the repository

bash
git clone https://github.com/your-username/aimatrix-backend.git
cd aimatrix-backend
Install dependencies

bash
npm install
Environment Configuration
Create .env file:

env
MONGODB_URI=mongodb://localhost:27017/aimatrix
RESEND_API_KEY=your_resend_api_key
PORT=3000
NODE_ENV=development
ADMIN_EMAIL=admin@aimatrix.example
Start the server

bash
# Development
npm run dev

# Production
npm start
🔧 API Endpoints
Health Check
GET /health - Server status

Analytics
GET /api/analytics - Get submission statistics

Contact Form
POST /api/contact - Submit contact form

GET /api/contact - Get all submissions (Admin)

Email System
POST /api/emails/notify-submission - Send email notification

GET /api/emails/logs - Get email logs

GET /api/emails/stats - Get email statistics

Admin
GET /admin - Admin dashboard

GET /api/docs - API documentation

📊 Database Schema
Contact Submissions
javascript
{
  name: String,
  email: String,
  message: String,
  createdAt: Date,
  status: String
}
Email Logs
javascript
{
  recipient: String,
  subject: String,
  status: String,
  messageId: String,
  createdAt: Date
}
🚀 Deployment
Deploy to Render:

Connect GitHub repository to Render

Set environment variables

Deploy automatically

Live API: https://aimatrix-backend-6t9i.onrender.com

🔒 Environment Variables
Variable	Description	Required
MONGODB_URI	MongoDB connection string	Yes
RESEND_API_KEY	Resend.com API key	Yes
PORT	Server port (default: 3000)	No
NODE_ENV	Environment (development/production)	No
ADMIN_EMAIL	Admin notification email	No
📧 Email System
The backend uses Resend.com for email notifications:

Contact Form Notifications: Automatic emails on form submission

HTML Templates: Professional email templates

Email Logging: Track all sent emails

Delivery Status: Monitor email delivery

🛡 Security Features
CORS configuration

Input validation and sanitization

Rate limiting (optional)

Error handling middleware

Secure headers

📈 Monitoring
Health check endpoints

Request logging

Error tracking

Performance monitoring
