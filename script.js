const API_URL = "https://aimatrix-backend-6t9i.onrender.com"; // Your actual backend URL

// 1. Handle Contact Form
const contactForm = document.getElementById('contact-form'); // Ensure your HTML form has id="contact-form"
if (contactForm) {
    contactForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = contactForm.querySelector('button');
        const originalText = submitBtn.innerText;
        submitBtn.innerText = "Sending...";
        
        const formData = {
            name: document.getElementById('name').value,
            email: document.getElementById('email').value,
            message: document.getElementById('message').value
        };

        try {
            const res = await fetch(`${API_URL}/api/contact`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            const data = await res.json();
            alert(data.message);
            contactForm.reset();
        } catch (error) {
            console.error(error);
            alert("Error sending message.");
        } finally {
            submitBtn.innerText = originalText;
        }
    });
}

// 2. Handle Payments (Razorpay)
// Call this function when a user clicks a "Buy" button
async function initiatePayment(planAmount, planName) {
    try {
        // Step 1: Create Order on Backend
        const res = await fetch(`${API_URL}/api/create-order`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount: planAmount * 100 }) // Convert to paise
        });
        const order = await res.json();

        // Step 2: Open Razorpay Checkout
        var options = {
            "key": "YOUR_RAZORPAY_KEY_ID", // Replace with your PUBLIC Key ID from Razorpay
            "amount": order.amount, 
            "currency": "INR",
            "name": "AIMatrix",
            "description": `Upgrade to ${planName}`,
            "order_id": order.id, 
            "handler": async function (response) {
                // Step 3: Verify Payment on Backend
                const verifyRes = await fetch(`${API_URL}/api/verify-payment`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(response)
                });
                const verifyData = await verifyRes.json();
                
                if (verifyData.status === 'success') {
                    alert("Payment Successful! Welcome to " + planName);
                    // Redirect to dashboard
                    // window.location.href = "/dashboard.html";
                } else {
                    alert("Payment verification failed.");
                }
            },
            "theme": { "color": "#3399cc" }
        };
        var rzp1 = new Razorpay(options);
        rzp1.open();
    } catch (err) {
        console.error("Payment failed:", err);
        alert("Could not initiate payment. Check console.");
    }
}

// Attach Payment Function to Buttons (Add IDs to your buttons in HTML)
const growthBtn = document.getElementById('buy-growth');
if (growthBtn) {
    growthBtn.onclick = () => initiatePayment(29999, "Growth Plan");
}

const starterBtn = document.getElementById('buy-starter');
if (starterBtn) {
    starterBtn.onclick = () => initiatePayment(9999, "Starter Plan");
}
