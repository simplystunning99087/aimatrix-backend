export default async function handler(req, res) {
  if (req.method !== 'POST')
    return res.status(405).json({ error: 'Method not allowed' });

  const PY = process.env.PYTHON_API_URL;

  const r = await fetch(`${PY}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req.body)
  });

  const json = await r.json();
  return res.status(r.status).json(json);
}
