async function predictMessage() {
  const text = document.getElementById("message").value;

  const response = await fetch("https://aimatrix-backend-6t9i.onrender.com/predict", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ text })
  });

  const data = await response.json();

  console.log("API Response:", data);

  // Show result on page
  document.getElementById("api-output").innerText =
    `Score: ${data.score} (Processed: ${data.input})`;
}
