// CONFIGURATION
const API_BASE_URL = "https://aimatrix-backend-6t9i.onrender.com"; // Your Render Backend URL

// --- 1. CONTACT FORM LOGIC ---
const contactForm = document.getElementById('contact-form');
if (contactForm) {
    contactForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = contactForm.querySelector('button');
        const originalText = btn.innerText;
        btn.innerText = "Sending...";

        const formData = {
            name: document.getElementById('name').value,
            email: document.getElementById('email').value,
            message: document.getElementById('message').value
        };

        try {
            const res = await fetch(`${API_BASE_URL}/api/contact`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            const data = await res.json();
            
            if (res.ok) {
                alert("Success: " + data.message);
                contactForm.reset();
            } else {
                alert("Error: " + data.error);
            }
        } catch (err) {
            console.error(err);
            alert("Network error. Please try again.");
        } finally {
            btn.innerText = originalText;
        }
    });
}

// --- 2. LOGIN LOGIC ---
// Ensure your Login HTML form has id="login-form"
const loginForm = document.getElementById('login-form');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        try {
            const res = await fetch(`${API_BASE_URL}/api/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const data = await res.json();

            if (res.ok) {
                // Save user info to LocalStorage to keep them "logged in" on frontend
                localStorage.setItem('user', JSON.stringify(data.user));
                alert("Login Successful!");
                window.location.href = "dashboard.html"; // Redirect to dashboard
            } else {
                alert(data.error);
            }
        } catch (err) {
            console.error(err);
            alert("Login failed. Check console.");
        }
    });
}

// --- 3. REGISTER LOGIC ---
// Ensure your Register HTML form has id="register-form"
const registerForm = document.getElementById('register-form');
if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('name').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        try {
            const res = await fetch(`${API_BASE_URL}/api/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password })
            });
            const data = await res.json();

            if (res.ok) {
                alert("Account created! Please login.");
                window.location.href = "login.html";
            } else {
                alert(data.error);
            }
        } catch (err) {
            console.error(err);
            alert("Registration failed.");
        }
    });
}

// --- 4. DASHBOARD CHECK ---
// Add this to dashboard.html script section to protect it
if (window.location.pathname.includes('dashboard.html')) {
    const user = JSON.parse(localStorage.getItem('user'));
    if (!user) {
        alert("You must be logged in to view this page.");
        window.location.href = "login.html";
    } else {
        // Optional: Display user name
        const userNameDisplay = document.getElementById('user-name-display');
        if (userNameDisplay) userNameDisplay.innerText = user.name;
    }
}

// --- 5. SYSTEM STATUS CHECKER ---
// This runs automatically when the page loads
async function checkSystemStatus() {
    const statusText = document.getElementById('system-status') || document.getElementById('backend-status'); 
    const statusIcon = document.getElementById('status-icon'); // If you have an icon
    
    // Check if elements exist to avoid errors
    if (!statusText) return;

    statusText.innerText = "Checking connection...";
    
    try {
        // We fetch the root URL which returns {status: "active"}
        const res = await fetch(`${API_BASE_URL}/`);
        
        if (res.ok) {
            statusText.innerText = "Online & Operational";
            statusText.style.color = "green";
            if(statusIcon) statusIcon.style.color = "green";
        } else {
            throw new Error("Backend returned error");
        }
    } catch (err) {
        console.error("Health check failed:", err);
        statusText.innerText = "System Offline (Maintenance)";
        statusText.style.color = "red";
    }
}

// Run the check immediately
checkSystemStatus();
