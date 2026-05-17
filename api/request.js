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

const GRADE_SYSTEM = `You are a PTE Academic grader. Apply official PTE rubrics STRICTLY.

For type "swt" (Summarize Written Text), score:
  - Form: 1 sentence = 1 pt, anything else = 0
  - Length: 5-75 words inclusive = 1 pt, otherwise 0
  - Content: captures main idea + key supporting tension = 0-2
  - Grammar: 0-2
  - Vocabulary range: 0-1
  TOTAL /7. Set correct=true if total >= 5.

For type "essay", score:
  - Content (addresses prompt fully + question type): 0-3
  - Form (200-300 words AND 5 paragraphs): 0-2
  - Development / Structure / Coherence: 0-2
  - Grammar: 0-2
  - Linguistic range (variety of sentence structures): 0-2
  - Vocabulary range (unique high-utility words): 0-2
  - Spelling: 0-2
  TOTAL /15. Set correct=true if total >= 10.

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

export default async function handler(req, res) {
  if (req.method === 'GET') {
    return res.status(200).json({
      ok: true,
      msg: 'PteracAI LLM endpoint. POST with headers x-provider, x-api-key, x-model.',
      providers: Object.keys(DEFAULT_MODELS),
    });
  }
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'method not allowed' });
  }

  const provider = (req.headers['x-provider'] || '').toString().toLowerCase();
  const apiKey = (req.headers['x-api-key'] || '').toString();
  const model = (req.headers['x-model'] || '').toString() || DEFAULT_MODELS[provider];

  if (!provider || !DEFAULT_MODELS[provider]) {
    return res.status(400).json({
      error: `missing or unsupported x-provider header. Use one of: ${Object.keys(DEFAULT_MODELS).join(', ')}`,
    });
  }
  if (!apiKey) {
    return res.status(401).json({ error: 'missing x-api-key header. Configure your key in Settings.' });
  }

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
      return res.status(200).json({ ok: true, question: parseJSON(text) });
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
