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

DROP POLICY IF EXISTS "anon can read non-hidden community questions"
  ON community_questions;
CREATE POLICY "anon can read non-hidden community questions"
  ON community_questions FOR SELECT
  USING (hidden = false);

-- Writes happen only from the serverless function using the service-role key,
-- which bypasses RLS automatically.

COMMENT ON TABLE community_questions IS
  'Crowd-grown question bank. Every AI-generated follow-up is saved (deduped by content hash). Anonymous — no user IDs stored.';

-- ---------------------------------------------------------------------------
-- Tailored tips cache: each question's LLM-generated tips computed ONCE
-- across all users, then served instantly to everyone afterward.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tailored_tips (
  question_id   text PRIMARY KEY,            -- seed bank id (e.g. r-mcq-001) or community 'c-<uuid>'
  tips          jsonb NOT NULL,              -- {"tips": ["...", "...", "..."]}
  hit_count     integer NOT NULL DEFAULT 0,  -- how many users got served from cache
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE tailored_tips ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon can read tailored tips"
  ON tailored_tips;
CREATE POLICY "anon can read tailored tips"
  ON tailored_tips FOR SELECT
  USING (true);

COMMENT ON TABLE tailored_tips IS
  'Per-question LLM tips, computed once across all users. Cache hit = instant + zero cost.';

-- ---------------------------------------------------------------------------
-- Access requests: users who want to sign in with Google but aren't yet
-- approved as Test Users in the OAuth consent screen. Owner reviews this
-- table, manually adds approved emails as Test Users in Google Cloud
-- Console, then emails the requester to let them know.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS access_requests (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email          text NOT NULL,
  name           text,
  message        text,
  status         text NOT NULL DEFAULT 'pending', -- 'pending' | 'approved' | 'rejected'
  requested_at   timestamptz NOT NULL DEFAULT now(),
  reviewed_at    timestamptz,
  reviewer_note  text
);

-- One row per (email, pending) — re-request updates rather than duplicates
CREATE UNIQUE INDEX IF NOT EXISTS access_requests_email_pending_unique
  ON access_requests (email)
  WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS access_requests_status_idx
  ON access_requests (status, requested_at DESC);

-- No public reads. Only the service-role key (used server-side) can read or
-- write this table. Reviewer accesses rows via the Supabase dashboard.
ALTER TABLE access_requests ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "no public access to access_requests"
  ON access_requests;
-- Intentionally no policies — RLS denies everything; only service-role bypasses.

COMMENT ON TABLE access_requests IS
  'Sign-in access requests. While the OAuth app is in test mode, users not yet on the Test Users list request access here. Reviewer adds approved emails to Google Cloud Console manually and updates status.';
