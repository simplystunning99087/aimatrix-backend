// api/contact.js
export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const { name, email, message } = req.body || {};
  if (!name || !email || !message) return res.status(400).json({ error: 'name,email,message required' });

  const SENDGRID_API_KEY = process.env.SENDGRID_API_KEY;
  const MAIL_TO = process.env.MAIL_TO;
  if (!SENDGRID_API_KEY || !MAIL_TO) return res.status(500).json({ error: 'Email not configured' });

  const payload = {
    personalizations: [{ to: [{ email: MAIL_TO }] }],
    from: { email: process.env.MAIL_FROM || 'no-reply@aimatrix.example' },
    subject: `New contact from ${name}`,
    content: [{ type: 'text/plain', value: `Name: ${name}\nEmail: ${email}\n\n${message}` }]
  };

  const r = await fetch('https://api.sendgrid.com/v3/mail/send', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${SENDGRID_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });

  if (!r.ok) {
    const errText = await r.text();
    return res.status(502).json({ error: 'SendGrid error', detail: errText });
  }
  return res.json({ success: true });
}
