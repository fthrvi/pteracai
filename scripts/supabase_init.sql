-- PteracAI community question bank schema.
--
-- One table. Stores every AI-generated follow-up question silently.
-- Future visitors can pull from this bank in addition to the seed bank.
--
-- Setup: paste into Supabase → SQL Editor → run once.

CREATE TABLE IF NOT EXISTS community_questions (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  test            text NOT NULL,                 -- 'pte' | 'ielts'
  section         text NOT NULL,                 -- 'reading' | 'listening' | 'writing' | 'speaking'
  type            text NOT NULL,                 -- 'mcq_single' | 'reorder' | 'fib' | ...
  topic           text,
  data            jsonb NOT NULL,                -- the full question object (passage, options, answer, explanation, trap, ...)
  content_hash    text NOT NULL,                 -- sha256 of canonical content for dedup
  attempts_count  integer NOT NULL DEFAULT 0,
  correct_count   integer NOT NULL DEFAULT 0,
  reports_count   integer NOT NULL DEFAULT 0,
  hidden          boolean NOT NULL DEFAULT false,-- auto-hide on 3+ reports or manual moderation
  created_at      timestamptz NOT NULL DEFAULT now()
);

-- Dedup: same content (passage + question + options) only saved once
CREATE UNIQUE INDEX IF NOT EXISTS community_questions_content_hash_unique
  ON community_questions (content_hash);

-- Fast lookup by test/section/type for the picker
CREATE INDEX IF NOT EXISTS community_questions_filter_idx
  ON community_questions (test, section, type, hidden);

-- Allow anonymous client-side reads via the anon key (we'll exclude hidden rows
-- in the API layer for cleanliness)
ALTER TABLE community_questions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon can read non-hidden community questions"
  ON community_questions FOR SELECT
  USING (hidden = false);

-- Writes happen only from the serverless function using the service-role key,
-- which bypasses RLS automatically.

COMMENT ON TABLE community_questions IS
  'Crowd-grown question bank. Every AI-generated follow-up is saved (deduped by content hash). Anonymous — no user IDs stored.';
