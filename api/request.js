// PteracAI Vercel serverless function — BYOK (bring your own key).
//
// The deployed site is FREE to host because each request uses the
// visitor's own API key. Supports three providers:
//   - anthropic   (Claude)
//   - openai      (GPT)
//   - openrouter  (proxy to many models — Gemini, Llama, Mistral, etc.)
//
// Request headers (sent by the browser):
//   x-provider:  'anthropic' | 'openai' | 'openrouter'
//   x-model:     model id for that provider
//   x-api-key:   the visitor's API key
//
// Body: same as the local file-bridge — { kind: 'followup'|'grade', ... }
//
// PRIVACY:
//   - The key passes through this function only to be forwarded
//     to the provider. We DO NOT log, persist, or transmit it anywhere else.
//   - The full source of this file is in the public GitHub repo so anyone
//     can verify.

import Anthropic from '@anthropic-ai/sdk';
import OpenAI from 'openai';
import { createHash } from 'crypto';

const FOLLOWUP_SYSTEM = `You are a PTE Academic question generator. Given a question the user got wrong, generate ONE new question of the SAME type and SAME topic that tests the SAME underlying skill, but with DIFFERENT content.

Respond with a single JSON object matching the schema for the requested type. NO markdown fences, NO commentary, NO preamble — just the JSON.

Schemas by type:

mcq_single:
{
  "id": "fu-<8 random chars>",
  "section": "reading",
  "type": "mcq_single",
  "topic": "<same as original>",
  "passage": "<150-250 word academic passage on a DIFFERENT subject from the original>",
  "question": "<the question stem>",
  "options": ["<option A>", "<option B>", "<option C>", "<option D>"],
  "answer": <index 0-3 of correct option>,
  "explanation": "<why the correct option is right AND why each wrong option fails — name them specifically>",
  "trap": "<the most-tempting wrong option and the cognitive shortcut that makes it tempting>"
}

reorder:
{
  "id": "fu-...", "section": "reading", "type": "reorder", "topic": "...",
  "paragraphs": ["<para in jumbled display order>", ...],
  "answer": [<indices into paragraphs giving the CORRECT order>],
  "explanation": "<sequence logic: topic sentence + connectors + pronouns>",
  "trap": "<the most likely mis-placement>"
}

fib:
{
  "id": "fu-...", "section": "reading", "type": "fib", "topic": "...",
  "text_parts": ["<text before blank 1>", "<text between blank 1 and 2>", ..., "<text after last blank>"],
  "options": [["a","b","c","d"], ["a","b","c","d"], ...],
  "answer": [<index per blank>],
  "explanation": "<collocation and grammar reasoning per blank>",
  "trap": "<the most plausible wrong choice per typical blank>"
}

wfd:
{
  "id": "fu-...", "section": "listening", "type": "wfd", "topic": "academic dictation",
  "audio_text": "<one academic sentence 8-15 words>",
  "answer": "<same as audio_text>",
  "explanation": "<spelling traps, homophones, plurals to watch for>"
}

swt:
{
  "id": "fu-...", "section": "writing", "type": "swt", "topic": "...",
  "passage": "<150-300 word academic passage with a main claim and a clear caveat>",
  "rubric": "ONE sentence, 5-75 words. Capture main claim + key caveat. Complex structure (although/while/despite).",
  "sample": "<an exemplar one-sentence summary you would write>",
  "grading_notes": "<what graders look for in this specific passage>"
}

essay:
{
  "id": "fu-...", "section": "writing", "type": "essay", "topic": "...",
  "prompt": "<the essay prompt ending with 'Write 200-300 words.'>",
  "rubric": "200-300 words. 5 paragraphs (intro/3 body/conclusion). Address the question type explicitly.",
  "grading_notes": "<scoring guide tailored to this prompt>"
}

QUALITY BAR (non-negotiable):
- Same TYPE and same TOPIC as the original.
- Passage / prompt / sentence is on a DIFFERENT subject domain from the original (e.g., if original was biology, do history).
- Difficulty: same band as original, OR slightly harder.
- Explanation NAMES specifically why each wrong option is wrong, not just "B is correct".
- For mcq_single, options must be plausible — no obvious throwaways.
- For reorder, the jumbled display order in "paragraphs" must NOT be the correct order (shuffle it).

Output ONLY the JSON object. No leading text. No trailing text. No code fences.`;

const GRADE_SYSTEM = `You are an English-test grader (PTE Academic AND IELTS Academic). Apply official rubrics STRICTLY based on the type of task you're grading.

For type "swt" (Summarize Written Text — PTE), score:
  - Form: 1 sentence = 1 pt, anything else = 0
  - Length: 5-75 words inclusive = 1 pt, otherwise 0
  - Content: captures main idea + key supporting tension = 0-2
  - Grammar: 0-2
  - Vocabulary range: 0-1
  TOTAL /7. Set correct=true if total >= 5.

For type "essay" (PTE 200-300 words, IELTS 250+ words):
  - Content/Task Response (addresses prompt fully + question type): 0-3
  - Form (length AND 5 paragraphs): 0-2
  - Development / Structure / Coherence: 0-2
  - Grammar: 0-2
  - Linguistic range (variety of sentence structures): 0-2
  - Vocabulary range (unique high-utility words): 0-2
  - Spelling: 0-2
  TOTAL /15. Set correct=true if total >= 10.

For type "task1" (IELTS Writing Task 1, 150+ words):
  - Task Achievement (covers key features + OVERVIEW paragraph): 0-3
  - Coherence/Cohesion: 0-2
  - Lexical Resource: 0-2
  - Grammar: 0-2
  TOTAL /9. Set correct=true if total >= 6. Penalize missing overview heavily.

For SPEAKING types ("read_aloud", "repeat_sentence", "describe_image", "retell_lecture", "answer_short", "ielts_part1", "ielts_part2", "ielts_part3"):
  Note: you receive a TRANSCRIPT (text), not audio. You can grade Content and (proxies for) Coherence/Vocabulary/Grammar from the transcript. You CANNOT directly grade pronunciation or oral fluency from text — be explicit about this limitation in your explanation.

  For "read_aloud" / "repeat_sentence": compute approximate word-match between the user's transcript and the original expected text. Score content as % of meaningful words matched. Explanation should name the words missed or substituted.

  For "describe_image" / "retell_lecture": score coverage of the key features expected, plus structural coherence (intro/body/conclusion present), plus vocabulary range observed in the transcript.

  For "answer_short": score 1 if the response is in the acceptable answer set or a clear semantic synonym, 0 otherwise.

  For IELTS Part 1/2/3: grade against IELTS speaking rubric proxies — Fluency/Coherence (length and flow of transcript), Lexical Resource (vocabulary variety), Grammar Range/Accuracy (sentence variety + errors). Pronunciation is NOT graded here.

  Score format for speaking: '8/12 content match' OR 'Fluency 6, Lexical 6.5, Grammar 6 — band ~6'. Use band-style for IELTS Speaking, percent-match for PTE Read Aloud/Repeat Sentence.

  In improvements, ALWAYS include: 'Pronunciation and oral fluency are not scored from the transcript. For a full assessment, use a tool that analyzes audio directly.'

Respond with a SINGLE JSON object — NO markdown, NO commentary:
{
  "correct": <bool>,
  "score": "<breakdown like '2/2 form, 1/1 length, 2/2 content, 2/2 grammar, 1/1 vocab = 8/7' OR '3/3 content, 2/2 form, ... = 13/15'>",
  "explanation": "<2-4 sentence summary of what worked and what fell short>",
  "improvements": [
    "<specific actionable suggestion — quote the user's exact text and propose a concrete change>",
    "<another specific suggestion>",
    "<another>"
  ]
}

Improvements must be SPECIFIC. BAD: "Improve vocabulary." GOOD: "Replace 'good' in sentence 2 with 'compelling' — vocab range is a separate scored dimension."

Output ONLY the JSON object.`;

const TIPS_SYSTEM = `You are a friendly PTE/IELTS coach giving short, specific tips for ONE question. Imagine you're sitting next to a student who's about to read it — what 2-3 things should they notice or watch out for FOR THIS QUESTION?

STRICT RULES:
1. Each tip MAX 15 words. Short. Direct.
2. Plain English — NO jargon. Don't say "discriminator", "paraphrase trap", "qualifier word".
3. Quote a specific word or phrase from the question/passage so the student knows where to look.
4. NEVER reveal the answer. NEVER say "the answer is X" or "pick the option about Y".
5. Different from generic strategy. Skip tips like "read carefully" or "find the topic sentence".

Examples of GOOD tips (short, specific, plain):
- 'Look at the word "However" in paragraph 2 — the answer flips after it.'
- 'Watch for "always" or "never" in the options — usually a trap.'
- 'The passage says "often" but option C says "always" — that's the catch.'
- 'Count the years: 1985, 1987, then "today" — order them in time.'

Examples of BAD tips (too generic, jargon-heavy, or vague):
- 'Identify the discriminator between paraphrased options.'  (jargon)
- 'Carefully consider the rhetorical structure.' (vague + academic)
- 'Note that hedging language indicates uncertainty.' (jargon)

Output ONLY this JSON, no markdown, no preamble:

{
  "tips": [
    "<tip 1 — short, plain, references something specific in the question>",
    "<tip 2>",
    "<tip 3 optional>"
  ]
}`;

const ANALYZE_SYSTEM = `You are an expert English-test coach analyzing a SINGLE wrong answer in detail. The user just got a question wrong and wants specific feedback on THEIR exact answer.

You receive: the question (with passage/prompt/options/correct answer) and what the user picked or wrote.

Your job: explain to the user, in 2-4 sentences total, why their SPECIFIC answer is wrong. Reference what they chose vs. what the correct answer is. Be concrete — point to specific words, ordering, or claims that make their choice fail.

Output a single JSON object — NO markdown, NO commentary:

{
  "diagnosis": "<1-2 sentence diagnosis: what their answer assumed or matched, and why that's wrong>",
  "comparison": "<1-2 sentence comparison: what the correct answer captures that theirs misses, with specific reference to the passage or prompt>",
  "fix": "<1 sentence: a concrete habit or check that would have caught this mistake — e.g., 'before picking, restate the option in your own words and re-check', or 'look for the time marker that pins this paragraph as third, not first'>"
}

For 'reorder' questions, reference the actual paragraph indices the user chose vs. the correct ordering — say things like "you put paragraph 3 first, but it starts with 'This phenomenon...' which references something earlier".

For 'mcq_single' / 'tfng', name the option letter the user chose AND the option letter that's correct, and explain the discriminator.

For 'fib' / 'matching_headings', identify which specific blanks/paragraphs they got wrong.

Output ONLY the JSON object. Keep total length under 100 words.`;

const COACH_SYSTEM = `You are an expert PTE Academic coach. The user has missed 3+ questions in a row on the SAME task type and topic. Your job: diagnose WHY they're failing, then give them targeted, surgical guidance.

You receive: the task type, the topic, and 3+ recent attempts (each with the original question and the user's wrong answer).

Diagnose:
- What specific cognitive pattern is failing? (e.g., "anchoring on passage wording without checking meaning", "confusing 'inference' with 'paraphrase'", "missing the caveat in summarize-written-text", "ignoring connector words in reorder")
- Is this a knowledge gap (don't know the rule) or a habit gap (knows the rule, fails to apply under pressure)?

Output a single JSON object — NO markdown, NO commentary:

{
  "diagnosis": "<1-2 sentence summary of the specific failure pattern, referencing what you saw in their wrong answers>",
  "micro_tips": [
    "<actionable tip targeting the pattern — quote a specific wrong answer of theirs if relevant>",
    "<another tip>",
    "<another tip — max 4 total>"
  ],
  "drill_focus": "<one short sentence describing what kind of question they should try next to break the pattern, e.g., 'try a re-order paragraph where the topic sentence uses no time markers — force pronoun-tracking instead'>"
}

Be SPECIFIC. BAD: "Read the passage more carefully." GOOD: "In question 2 you picked option C because it used the word 'rapid' from the passage — but the passage said 'rapid decline' while option C said 'rapid growth'. You're matching on words, not meaning. Before picking, restate the option's claim in your own words and re-check against the passage."

Output ONLY the JSON object.`;

const DEFAULT_MODELS = {
  anthropic: 'claude-sonnet-4-6',
  openai: 'gpt-4o-mini',
  openrouter: 'anthropic/claude-sonnet-4',
};

// Free-tier model cascade: OpenRouter falls back automatically if the
// first is rate-limited. All marked :free, no token cost.
// Currently-available OpenRouter free models (the lineup rotates — check
// /api/v1/models for current options if these stop working).
// Picked for diversity: 3 different providers so rate-limits cascade better.
const FREE_TIER_MODELS = [
  'openai/gpt-oss-120b:free',
  'deepseek/deepseek-v4-flash:free',
  'google/gemma-4-31b-it:free',
];

export default async function handler(req, res) {
  if (req.method === 'GET') {
    return res.status(200).json({
      ok: true,
      msg: 'PteracAI LLM endpoint. POST with headers x-provider, x-api-key, x-model. Or POST with no key headers to use the shared free tier (when configured).',
      providers: Object.keys(DEFAULT_MODELS),
      free_tier_available: Boolean(process.env.OPENROUTER_FREE_KEY),
    });
  }
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'method not allowed' });
  }

  let provider = (req.headers['x-provider'] || '').toString().toLowerCase();
  let apiKey = (req.headers['x-api-key'] || '').toString();
  let model = (req.headers['x-model'] || '').toString();
  let usedFreeTier = false;

  // Free-tier fallback: if the visitor sent no API key but the server
  // has OPENROUTER_FREE_KEY configured, route to the shared free key.
  if (!apiKey && process.env.OPENROUTER_FREE_KEY) {
    apiKey = process.env.OPENROUTER_FREE_KEY;
    provider = 'openrouter_free';
    model = ''; // free tier uses cascade, not a single model
    usedFreeTier = true;
  }

  if (!usedFreeTier && (!provider || !DEFAULT_MODELS[provider])) {
    return res.status(400).json({
      error: `missing or unsupported x-provider header. Use one of: ${Object.keys(DEFAULT_MODELS).join(', ')}`,
    });
  }
  if (!apiKey) {
    return res.status(401).json({
      error: 'No AI key configured. Add your own key in Settings, or contact the site owner to enable free tier.',
      free_tier_available: false,
    });
  }
  if (!usedFreeTier && !model) model = DEFAULT_MODELS[provider];

  let payload;
  try {
    payload = typeof req.body === 'string' ? JSON.parse(req.body) : req.body;
  } catch (e) {
    return res.status(400).json({ error: 'invalid json body' });
  }
  if (!payload || typeof payload !== 'object') {
    return res.status(400).json({ error: 'missing body' });
  }

  const { kind } = payload;
  try {
    if (kind === 'followup') {
      const userMsg = buildFollowupUserMsg(payload);
      const text = await callLLM({ provider, apiKey, model, system: FOLLOWUP_SYSTEM, userMsg });
      const question = parseJSON(text);
      // Fire-and-forget save to community bank (don't block user response)
      saveToCommunityBank(payload, question).catch((e) =>
        console.warn('community save failed:', e?.message || e)
      );
      return res.status(200).json({ ok: true, question });
    }
    if (kind === 'grade') {
      const userMsg = buildGradeUserMsg(payload);
      const text = await callLLM({ provider, apiKey, model, system: GRADE_SYSTEM, userMsg });
      return res.status(200).json({ ok: true, grading: parseJSON(text) });
    }
    if (kind === 'coach') {
      const userMsg = buildCoachUserMsg(payload);
      const text = await callLLM({ provider, apiKey, model, system: COACH_SYSTEM, userMsg });
      return res.status(200).json({ ok: true, coaching: parseJSON(text) });
    }
    if (kind === 'analyze') {
      const userMsg = buildAnalyzeUserMsg(payload);
      const text = await callLLM({ provider, apiKey, model, system: ANALYZE_SYSTEM, userMsg });
      return res.status(200).json({ ok: true, analysis: parseJSON(text) });
    }
    if (kind === 'tips') {
      // Use content hash as cache key — same passage/options = same tips,
      // regardless of which id system the question came through (LLM-generated
      // 'fu-xxx', community 'c-uuid', or seed bank 'r-mcq-001').
      const cacheKey = questionContentHash(payload.question);
      if (cacheKey) {
        const cached = await getCachedTips(cacheKey);
        if (cached) {
          return res.status(200).json({ ok: true, tailored_tips: cached, cached: true });
        }
      }
      const userMsg = JSON.stringify({
        question: payload.question,
        instruction: 'Generate 2-3 strategic tips specific to this question. NEVER reveal the answer. Output ONLY the JSON.',
      });
      const text = await callLLM({ provider, apiKey, model, system: TIPS_SYSTEM, userMsg });
      const tipsObj = parseJSON(text);
      if (cacheKey && tipsObj?.tips) {
        saveTipsToCache(cacheKey, tipsObj).catch((e) =>
          console.warn('tips cache save failed:', e?.message || e)
        );
      }
      return res.status(200).json({ ok: true, tailored_tips: tipsObj });
    }
    return res.status(400).json({ error: `unknown kind: ${kind}` });
  } catch (err) {
    // Never leak the key. Sanitize messages.
    const msg = redact(err?.message || 'LLM call failed', apiKey);
    console.error('LLM error:', msg);
    return res.status(500).json({ error: msg });
  }
}

function buildFollowupUserMsg(payload) {
  return JSON.stringify({
    section: payload.section,
    type: payload.type,
    topic: payload.topic,
    original_question: payload.original_question,
    instruction:
      'Generate ONE new question of the same type and topic but DIFFERENT content. Return ONLY the JSON object matching the schema for this type.',
  });
}

function buildGradeUserMsg(payload) {
  return JSON.stringify({
    type: payload.type,
    question: payload.question,
    user_answer: payload.user_answer,
    instruction:
      'Grade strictly per PTE rubric for this type. Return ONLY the grading JSON object.',
  });
}

function buildAnalyzeUserMsg(payload) {
  return JSON.stringify({
    question: payload.question,
    user_answer: payload.user_answer,
    instruction:
      'Analyze why this specific answer is wrong. Output ONLY the analysis JSON object.',
  });
}

function buildCoachUserMsg(payload) {
  return JSON.stringify({
    section: payload.section,
    type: payload.type,
    topic: payload.topic,
    consecutive_wrong: payload.consecutive_wrong,
    recent_attempts: payload.recent_attempts, // [{question, user_answer, correct_answer}]
    instruction:
      'Diagnose the user\'s specific failure pattern across these attempts. Return ONLY the coaching JSON.',
  });
}

async function callLLM({ provider, apiKey, model, system, userMsg }) {
  if (provider === 'openrouter_free') {
    // Explicit per-model retry — OpenRouter's built-in cascade doesn't fall
    // through reliably on 429s. We try each free model in sequence.
    const errors = [];
    for (const m of FREE_TIER_MODELS) {
      try {
        const resp = await fetch('https://openrouter.ai/api/v1/chat/completions', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${apiKey}`,
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://pteracai.vercel.app',
            'X-Title': 'PteracAI (free tier)',
          },
          body: JSON.stringify({
            model: m,
            max_tokens: 2000,
            messages: [
              { role: 'system', content: system },
              { role: 'user', content: userMsg },
            ],
          }),
        });
        if (!resp.ok) {
          const errText = await resp.text();
          errors.push(`${m}: ${resp.status}`);
          // Retry next model on rate-limit or upstream error
          if (resp.status === 429 || resp.status === 502 || resp.status === 503) continue;
          throw new Error(`openrouter ${resp.status}: ${errText.slice(0, 200)}`);
        }
        const data = await resp.json();
        const content = data.choices?.[0]?.message?.content;
        if (content) return content;
        errors.push(`${m}: empty response`);
      } catch (e) {
        errors.push(`${m}: ${e.message}`);
      }
    }
    throw new Error(`All free-tier models failed. ${errors.join(' | ')}`);
  }

  if (provider === 'anthropic') {
    const client = new Anthropic({ apiKey });
    const resp = await client.messages.create({
      model,
      max_tokens: 2500,
      system: [
        { type: 'text', text: system, cache_control: { type: 'ephemeral' } },
      ],
      messages: [{ role: 'user', content: userMsg }],
    });
    return resp.content.find((b) => b.type === 'text')?.text || '';
  }

  if (provider === 'openai') {
    const client = new OpenAI({ apiKey });
    const resp = await client.chat.completions.create({
      model,
      max_tokens: 2500,
      response_format: { type: 'json_object' },
      messages: [
        { role: 'system', content: system + '\n\nReturn ONLY a JSON object.' },
        { role: 'user', content: userMsg },
      ],
    });
    return resp.choices[0]?.message?.content || '';
  }

  if (provider === 'openrouter') {
    // OpenRouter uses the OpenAI-compatible API surface.
    const resp = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://github.com/', // openrouter likes a referer
        'X-Title': 'PteracAI',
      },
      body: JSON.stringify({
        model,
        max_tokens: 2500,
        messages: [
          { role: 'system', content: system },
          { role: 'user', content: userMsg },
        ],
      }),
    });
    if (!resp.ok) {
      const errText = await resp.text();
      throw new Error(`openrouter ${resp.status}: ${errText.slice(0, 200)}`);
    }
    const data = await resp.json();
    return data.choices?.[0]?.message?.content || '';
  }

  throw new Error(`unsupported provider: ${provider}`);
}

function parseJSON(text) {
  let s = (text || '').trim();
  s = s.replace(/^```(?:json)?\s*/i, '').replace(/\s*```\s*$/, '');
  const first = s.indexOf('{');
  const last = s.lastIndexOf('}');
  if (first !== -1 && last !== -1 && last > first) {
    s = s.slice(first, last + 1);
  }
  return JSON.parse(s);
}

function redact(str, secret) {
  if (!secret || secret.length < 8) return str;
  return str.split(secret).join('[REDACTED-KEY]');
}

// Save an AI-generated follow-up question to the community bank (Supabase).
// Fire-and-forget — caller should .catch() any rejection. Anonymous, deduped
// by content hash. Silently no-ops if Supabase isn't configured.
async function saveToCommunityBank(payload, question) {
  // Accept any of the standard Supabase env var names. Vercel's official
  // Supabase integration adds SERVICE_ROLE_KEY; new Supabase dashboards add
  // SECRET_KEY; some setups use plain SERVICE_KEY.
  const supabaseUrl = process.env.SUPABASE_URL;
  const supabaseKey =
    process.env.SUPABASE_SERVICE_ROLE_KEY ||
    process.env.SUPABASE_SECRET_KEY ||
    process.env.SUPABASE_SERVICE_KEY;
  if (!supabaseUrl || !supabaseKey) return;
  if (!question || typeof question !== 'object') return;

  // Which test does this belong to? Heuristic: original question id prefix.
  const test = (payload.original_question?.id || '').startsWith('i-') ? 'ielts' : 'pte';
  const section = question.section || payload.section || 'reading';
  const type = question.type || payload.type || 'mcq_single';
  const topic = question.topic || payload.topic || '';

  // Canonical content hash for dedup — same content saved once across all users.
  const canonical = JSON.stringify({
    passage: question.passage || '',
    question: question.question || '',
    options: question.options || [],
    prompt: question.prompt || '',
    paragraphs: question.paragraphs || [],
    text_parts: question.text_parts || [],
    audio_text: question.audio_text || '',
    statement: question.statement || '',
    headings: question.headings || [],
  });
  const content_hash = createHash('sha256').update(canonical).digest('hex');

  const url = `${supabaseUrl}/rest/v1/community_questions?on_conflict=content_hash`;
  await fetch(url, {
    method: 'POST',
    headers: {
      apikey: supabaseKey,
      Authorization: `Bearer ${supabaseKey}`,
      'Content-Type': 'application/json',
      Prefer: 'resolution=ignore-duplicates,return=minimal',
    },
    body: JSON.stringify({ test, section, type, topic, data: question, content_hash }),
  });
}

// Stable content hash for a question. Same content = same hash regardless of
// id system. Used as the cache key for tailored_tips so all users (generator,
// community fetchers, seed-bank users) share the same cached tips.
function questionContentHash(q) {
  if (!q || typeof q !== 'object') return null;
  const canonical = JSON.stringify({
    passage: q.passage || '',
    question: q.question || '',
    options: q.options || [],
    prompt: q.prompt || '',
    paragraphs: q.paragraphs || [],
    text_parts: q.text_parts || [],
    audio_text: q.audio_text || '',
    statement: q.statement || '',
    headings: q.headings || [],
  });
  return createHash('sha256').update(canonical).digest('hex');
}

// Tip cache helpers — global tailored-tips memoization keyed by content hash.
function _supabaseCreds() {
  return {
    url: process.env.SUPABASE_URL,
    key:
      process.env.SUPABASE_SERVICE_ROLE_KEY ||
      process.env.SUPABASE_SECRET_KEY ||
      process.env.SUPABASE_SERVICE_KEY,
  };
}

async function getCachedTips(qid) {
  const { url: supabaseUrl, key: supabaseKey } = _supabaseCreds();
  if (!supabaseUrl || !supabaseKey || !qid) return null;
  try {
    const r = await fetch(
      `${supabaseUrl}/rest/v1/tailored_tips?question_id=eq.${encodeURIComponent(qid)}&select=tips`,
      { headers: { apikey: supabaseKey, Authorization: `Bearer ${supabaseKey}` } }
    );
    if (!r.ok) return null;
    const rows = await r.json();
    return rows[0]?.tips || null;
  } catch {
    return null;
  }
}

async function saveTipsToCache(qid, tipsObj) {
  const { url: supabaseUrl, key: supabaseKey } = _supabaseCreds();
  if (!supabaseUrl || !supabaseKey || !qid) return;
  // Upsert — first-write wins, conflict ignores. Tips are stable per question.
  const url = `${supabaseUrl}/rest/v1/tailored_tips?on_conflict=question_id`;
  await fetch(url, {
    method: 'POST',
    headers: {
      apikey: supabaseKey,
      Authorization: `Bearer ${supabaseKey}`,
      'Content-Type': 'application/json',
      Prefer: 'resolution=ignore-duplicates,return=minimal',
    },
    body: JSON.stringify({ question_id: qid, tips: tipsObj }),
  });
}

async function incrementTipsHit(qid) {
  // Best-effort counter increment via RPC would be ideal but PostgREST PATCH
  // works fine if we read-then-write. Skipped to avoid extra request hop —
  // total hit count isn't load-bearing right now. Keeping helper stub for later.
  return;
}
