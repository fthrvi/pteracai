# PteracAI — Claude Code protocol

PteracAI is a local PTE practice app. The browser app handles the UI and
auto-grades objective questions. **You (Claude Code) are the LLM in the
loop** for two things:

1. **Generating follow-up questions** when the user gets a question wrong (mastery loop)
2. **Grading subjective writing** (Summarize Written Text, Essay)

The browser cannot call you directly. It uses a file bridge:

- Browser → POST `/api/request` → server appends to `data/requests.jsonl`
- You read `data/requests.jsonl`, find unprocessed requests, write
  responses to `data/responses.jsonl`
- Browser polls `/api/responses` every 1.5s and renders the reply

## The trigger phrase

When the user says any of these in the terminal, do the protocol below:

- "process pending pterac requests"
- "process pterac"
- "pterac process"

## Protocol

1. Read `data/requests.jsonl` and `data/responses.jsonl`.
2. Find every request whose `id` does NOT appear as a `request_id` in `data/responses.jsonl`.
3. For each unprocessed request, generate the appropriate response (see schemas below).
4. Append each response as a single JSON line to `data/responses.jsonl`.
5. Use a monotonically increasing `seq` integer (one greater than the max existing `seq`).
6. Print a short summary to the user: how many requests processed, of what kinds.

## Request kinds

### `kind: "followup"`

The user got a question wrong and wants a similar one to confirm mastery.

Request shape:
```json
{
  "id": "abc12345",
  "ts": 1700000000.0,
  "status": "pending",
  "kind": "followup",
  "original_qid": "r-mcq-001",
  "section": "reading",
  "type": "mcq_single",
  "topic": "main idea identification",
  "notes": "User got this wrong. Generate ONE new question...",
  "original_question": { ...full original question object... }
}
```

Response shape (append to `data/responses.jsonl`):
```json
{
  "seq": 1,
  "request_id": "abc12345",
  "question": {
    "id": "fu-abc12345",
    "section": "reading",
    "type": "mcq_single",
    "topic": "main idea identification",
    "passage": "...new passage...",
    "question": "What is the main idea?",
    "options": ["...", "...", "...", "..."],
    "answer": 2,
    "explanation": "...why C is correct, why others fail...",
    "trap": "...the most likely wrong choice and why people fall for it..."
  }
}
```

The `question` object must follow the schema for its `type` in `data/bank.json`:

- `mcq_single`: `passage`, `question`, `options[]`, `answer` (index), `explanation`, `trap`
- `reorder`: `paragraphs[]` (in jumbled order as displayed), `answer[]` (indices in correct order), `explanation`, `trap`
- `fib`: `text_parts[]` (N+1 strings around N blanks), `options[][]` (N arrays of choices), `answer[]` (N indices), `explanation`, `trap`
- `wfd`: `audio_text` (the sentence to dictate), `answer` (same text), `explanation`
- `swt`: `passage`, `rubric`, `sample`, `grading_notes`
- `essay`: `prompt`, `rubric`, `grading_notes`

**Quality bar for follow-ups:**
- Same `type` and same `topic` as the original
- DIFFERENT content (don't just reword the original passage)
- Test the SAME underlying skill (e.g., if original was main-idea identification with a science passage, follow-up is main-idea with a humanities passage)
- Difficulty: ~same as original, slightly harder is OK
- Include a real `explanation` that names *why* each wrong option is wrong, not just "C is correct"
- Include a `trap` field that names the most tempting wrong answer and the cognitive mistake behind it

### `kind: "grade"`

The user wrote a free-form response (SWT or Essay) and wants it graded.

Request shape:
```json
{
  "id": "def67890",
  "kind": "grade",
  "qid": "w-swt-001",
  "section": "writing",
  "type": "swt",
  "question": { ...full question object including rubric, sample, grading_notes... },
  "user_answer": "Although urban beekeeping..."
}
```

Response shape:
```json
{
  "seq": 2,
  "request_id": "def67890",
  "grading": {
    "correct": true,
    "score": "2/3 content, 1/2 form, 2/2 grammar = 5/7",
    "explanation": "Strong main idea capture and caveat. Sentence is grammatically clean. Minor: ...",
    "improvements": [
      "Tighten the opening clause — 'Although urban beekeeping has grown popular' could be 'Although urban beekeeping has grown'.",
      "Replace 'seeks to' with 'aims to' for variety since you used 'aims' earlier."
    ]
  }
}
```

**Grading rubrics — apply PTE standards strictly:**

- **SWT (Summarize Written Text):** 0-7 total. (1) ONE sentence only (0 or 1). (2) 5-75 words (0 or 1). (3) Captures main idea (0-2). (4) Grammar (0-2). (5) Vocabulary (0-1). `correct: true` requires ≥5/7.
- **Essay:** Score each 0-3: content, development/structure/coherence, form (200-300 words & paragraphs), grammar, vocabulary range, spelling. Plus 0-2 for linguistic range. Total /20. `correct: true` requires ≥14/20.

Always include 2-4 specific, actionable `improvements`. Don't say "improve vocabulary" — say "replace 'good' with 'compelling' in sentence 2."

## After processing

Print to the user something like:

> Processed 2 PteracAI requests: 1 follow-up question (reading/mcq_single), 1 essay grading. Browser should pick them up within 1.5s.

That's it. The browser handles all rendering.
