// Access-request endpoint. Users who can't sign in (not on the OAuth
// Test Users list) submit their email + optional name + reason here.
// Owner reviews via Supabase dashboard, manually approves in Google
// Cloud Console, then emails the requester back.
//
// POST /api/access-request
// Body: { email: string (required), name?: string, message?: string }
// Response: { ok: true } on success, { error: string } on failure.

export const config = { maxDuration: 10 };

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "POST only" });
  }

  let body = req.body;
  if (typeof body === "string") {
    try { body = JSON.parse(body); } catch { body = {}; }
  }
  body = body || {};

  const email = (body.email || "").toString().trim().toLowerCase();
  const name = (body.name || "").toString().trim().slice(0, 120) || null;
  const message = (body.message || "").toString().trim().slice(0, 600) || null;

  if (!email || !EMAIL_RE.test(email) || email.length > 254) {
    return res.status(400).json({ error: "A valid email is required." });
  }

  const SUPABASE_URL = process.env.SUPABASE_URL;
  const SUPABASE_KEY = process.env.SUPABASE_SERVICE_KEY
    || process.env.SUPABASE_SERVICE_ROLE_KEY
    || process.env.SUPABASE_SECRET_KEY;
  if (!SUPABASE_URL || !SUPABASE_KEY) {
    return res.status(500).json({ error: "Backend not configured." });
  }

  try {
    // Upsert: if there's already a pending request for this email, update it
    // rather than create a duplicate. The unique partial index on (email)
    // WHERE status='pending' enforces this at the DB level.
    const resp = await fetch(
      `${SUPABASE_URL}/rest/v1/access_requests?on_conflict=email`,
      {
        method: "POST",
        headers: {
          "apikey": SUPABASE_KEY,
          "authorization": `Bearer ${SUPABASE_KEY}`,
          "content-type": "application/json",
          "prefer": "resolution=merge-duplicates,return=minimal",
        },
        body: JSON.stringify({
          email,
          name,
          message,
          status: "pending",
          requested_at: new Date().toISOString(),
        }),
      },
    );

    if (!resp.ok) {
      // If the unique partial index rejected (duplicate pending), treat as success
      const errText = await resp.text();
      if (errText.includes("access_requests_email_pending_unique")) {
        return res.status(200).json({ ok: true, deduped: true });
      }
      return res.status(500).json({ error: `Could not save request: ${errText.slice(0, 200)}` });
    }

    return res.status(200).json({ ok: true });
  } catch (e) {
    return res.status(500).json({ error: e.message || "Network error" });
  }
}
