// PteracAI community question bank — read endpoint.
//
// Fetches AI-generated questions previously saved by other visitors.
// Anonymous reads via Supabase anon key (RLS filters out hidden rows).
//
// GET /api/community?test=pte&section=reading&type=mcq_single&limit=10
//   → { count, questions: [...] }
//
// Returns empty array if Supabase isn't configured — frontend falls back
// to seed bank only.

const DEFAULT_LIMIT = 30;
const MAX_LIMIT = 100;

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'method not allowed' });
  }

  const supabaseUrl = process.env.SUPABASE_URL;
  // For reads we can use either the anon/publishable key OR the secret key — anon
  // is enough since RLS allows SELECT on hidden=false rows. Accept multiple naming
  // conventions (Supabase-Vercel integration adds different sets of vars).
  const supabaseKey =
    process.env.SUPABASE_ANON_KEY ||
    process.env.SUPABASE_PUBLISHABLE_KEY ||
    process.env.SUPABASE_SERVICE_ROLE_KEY ||
    process.env.SUPABASE_SECRET_KEY ||
    process.env.SUPABASE_SERVICE_KEY;

  if (!supabaseUrl || !supabaseKey) {
    return res.status(200).json({ count: 0, questions: [], reason: 'community bank not configured' });
  }

  const test = (req.query.test || '').toString();
  const section = (req.query.section || '').toString();
  const type = (req.query.type || '').toString();
  const limit = Math.min(
    parseInt(req.query.limit, 10) || DEFAULT_LIMIT,
    MAX_LIMIT
  );

  if (!test || !section || !type) {
    return res.status(400).json({
      error: 'missing required query params: test, section, type',
    });
  }

  // Pull the most recent N matching questions
  const params = new URLSearchParams({
    select: 'id,data,attempts_count,correct_count,created_at',
    test: `eq.${test}`,
    section: `eq.${section}`,
    type: `eq.${type}`,
    hidden: 'eq.false',
    order: 'created_at.desc',
    limit: String(limit),
  });

  const url = `${supabaseUrl}/rest/v1/community_questions?${params}`;
  try {
    const r = await fetch(url, {
      headers: {
        apikey: supabaseKey,
        Authorization: `Bearer ${supabaseKey}`,
      },
    });
    if (!r.ok) {
      const text = await r.text();
      return res.status(502).json({ error: `supabase ${r.status}: ${text.slice(0, 200)}` });
    }
    const rows = await r.json();
    // Stamp each question with community: true so the picker can tag it visually
    const questions = rows.map((row) => ({
      ...row.data,
      id: `c-${row.id}`,
      community: true,
      attempts_count: row.attempts_count,
      correct_count: row.correct_count,
    }));
    return res.status(200).json({ count: questions.length, questions });
  } catch (e) {
    return res.status(500).json({ error: e?.message || 'fetch failed' });
  }
}
