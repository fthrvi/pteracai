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

  const sbHeaders = {
    "apikey": SUPABASE_KEY,
    "authorization": `Bearer ${SUPABASE_KEY}`,
    "content-type": "application/json",
  };

  try {
    // 1) Check whether this email already has a row — pending, approved, or rejected.
    //    Tell the user explicitly rather than silently creating duplicates.
    const existingResp = await fetch(
      `${SUPABASE_URL}/rest/v1/access_requests?email=eq.${encodeURIComponent(email)}&select=status,requested_at,reviewed_at&order=requested_at.desc&limit=1`,
      { headers: sbHeaders },
    );
    if (existingResp.ok) {
      const rows = await existingResp.json();
      if (rows && rows.length > 0) {
        const row = rows[0];
        if (row.status === "approved") {
          return res.status(200).json({
            ok: true,
            status: "approved",
            message: "You already have access — try signing in with Google. If it still fails, contact the site owner.",
          });
        }
        if (row.status === "pending") {
          return res.status(200).json({
            ok: true,
            status: "pending",
            message: "Your earlier request is still pending review. You'll get an email as soon as it's approved.",
          });
        }
        if (row.status === "rejected") {
          // Allow re-submission by updating the existing row back to pending
          // with the new message — gives the user another shot if they
          // include better context this time.
          await fetch(
            `${SUPABASE_URL}/rest/v1/access_requests?email=eq.${encodeURIComponent(email)}`,
            {
              method: "PATCH",
              headers: { ...sbHeaders, "prefer": "return=minimal" },
              body: JSON.stringify({
                status: "pending",
                message,
                name,
                requested_at: new Date().toISOString(),
                reviewed_at: null,
                reviewer_note: null,
              }),
            },
          );
          return res.status(200).json({
            ok: true,
            status: "resubmitted",
            message: "Re-submitted. You'll hear back by email within a day.",
          });
        }
      }
    }

    // 2) No existing row — insert a fresh pending one.
    const resp = await fetch(`${SUPABASE_URL}/rest/v1/access_requests`, {
      method: "POST",
      headers: { ...sbHeaders, "prefer": "return=minimal" },
      body: JSON.stringify({
        email,
        name,
        message,
        status: "pending",
        requested_at: new Date().toISOString(),
      }),
    });

    if (!resp.ok) {
      const errText = await resp.text();
      // Race: another request for same email landed between our check and insert.
      if (errText.includes("access_requests_email_pending_unique")) {
        return res.status(200).json({
          ok: true,
          status: "pending",
          message: "Your request is already pending review.",
        });
      }
      return res.status(500).json({ error: `Could not save request: ${errText.slice(0, 200)}` });
    }

    return res.status(200).json({
      ok: true,
      status: "submitted",
      message: "Request submitted. You'll hear back by email within a day.",
    });
  } catch (e) {
    return res.status(500).json({ error: e.message || "Network error" });
  }
}
