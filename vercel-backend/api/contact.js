export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const { name, email, message } = req.body || {};

  const SENDGRID_API_KEY = process.env.SENDGRID_API_KEY;
  const MAIL_TO = process.env.MAIL_TO;

  const payload = {
    personalizations: [{ to: [{ email: MAIL_TO }] }],
    from: { email: "no-reply@aimatrix.com" },
    subject: `New AIMatrix Contact From ${name}`,
    content: [{ type: 'text/plain', value: `Email: ${email}\n\n${message}` }]
  };

  const r = await fetch("https://api.sendgrid.com/v3/mail/send", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${SENDGRID_API_KEY}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!r.ok) {
    return res.status(500).json({ error: "Email failed" });
  }

  return res.json({ success: true });
}
