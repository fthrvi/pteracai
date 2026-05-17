// PteracAI — frontend logic
// Architecture: vanilla JS, no framework. Loads bank.json, renders one
// question at a time, grades auto-gradable types client-side, posts
// LLM-grading and follow-up requests to the local server, then polls
// /api/responses for Claude Code's reply.

const state = {
  bank: null,
  section: "reading",
  currentQ: null,
  currentFollowupOf: null,
  attempted: 0,
  correct: 0,
  streak: 0,
  responseSeq: 0,
  pollTimer: null,
  inflightById: new Map(),
};

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

// Safe DOM builder. Only sets attributes and appends text/Node children.
// No innerHTML escape hatch.
function el(tag, attrs, ...children) {
  const e = document.createElement(tag);
  if (attrs) {
    for (const [k, v] of Object.entries(attrs)) {
      if (k === "class") e.className = v;
      else if (k.startsWith("on") && typeof v === "function") e.addEventListener(k.slice(2), v);
      else e.setAttribute(k, v);
    }
  }
  for (const c of children) {
    if (c == null || c === false) continue;
    e.appendChild(typeof c === "string" || typeof c === "number"
      ? document.createTextNode(String(c))
      : c);
  }
  return e;
}

function clear(node) { node.replaceChildren(); }

// ---------- bootstrap ----------
async function boot() {
  const res = await fetch("/data/bank.json");
  state.bank = await res.json();
  bindSectionButtons();
  renderPicker();
  startPolling();
}

function bindSectionButtons() {
  $$(".section-btn[data-section]").forEach((b) => {
    b.addEventListener("click", () => {
      $$(".section-btn").forEach((x) => x.classList.remove("active"));
      b.classList.add("active");
      state.section = b.dataset.section;
      state.currentFollowupOf = null;
      renderPicker();
    });
  });
  $("#random-btn").addEventListener("click", () => pickRandom());
  $("#tips-nav").addEventListener("click", () => {
    $$(".section-btn").forEach((x) => x.classList.remove("active"));
    $("#tips-nav").classList.add("active");
    renderTipsView();
  });
  $("#settings-nav").addEventListener("click", () => {
    $$(".section-btn").forEach((x) => x.classList.remove("active"));
    $("#settings-nav").classList.add("active");
    renderSettingsView();
  });
}

// ---------- BYOK settings (localStorage) ----------
const SETTINGS_KEY = "pteracai_settings_v1";
const REPO_URL = "https://github.com/bbastola899/pteracai";

const PROVIDERS = {
  anthropic: {
    label: "Anthropic (Claude)",
    keyHint: "starts with sk-ant-api03-",
    getKeyUrl: "https://console.anthropic.com/settings/keys",
    models: [
      { id: "claude-sonnet-4-6", label: "Claude Sonnet 4.6 (recommended)" },
      { id: "claude-opus-4-7", label: "Claude Opus 4.7 (best quality, ~5x cost)" },
      { id: "claude-haiku-4-5-20251001", label: "Claude Haiku 4.5 (cheapest)" },
    ],
  },
  openai: {
    label: "OpenAI (GPT)",
    keyHint: "starts with sk-",
    getKeyUrl: "https://platform.openai.com/api-keys",
    models: [
      { id: "gpt-4o-mini", label: "gpt-4o-mini (recommended, cheap)" },
      { id: "gpt-4o", label: "gpt-4o (higher quality)" },
      { id: "gpt-4-turbo", label: "gpt-4-turbo" },
    ],
  },
  openrouter: {
    label: "OpenRouter (any model)",
    keyHint: "starts with sk-or-",
    getKeyUrl: "https://openrouter.ai/keys",
    models: [
      { id: "anthropic/claude-sonnet-4", label: "Claude Sonnet 4 (via OpenRouter)" },
      { id: "openai/gpt-4o-mini", label: "GPT-4o-mini (via OpenRouter)" },
      { id: "google/gemini-2.5-flash", label: "Gemini 2.5 Flash (via OpenRouter)" },
      { id: "meta-llama/llama-3.3-70b-instruct", label: "Llama 3.3 70B (via OpenRouter)" },
      { id: "mistralai/mistral-large", label: "Mistral Large (via OpenRouter)" },
    ],
  },
};

function loadSettings() {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (!raw) return null;
    const s = JSON.parse(raw);
    if (s && s.provider && s.apiKey) return s;
    return null;
  } catch (e) {
    return null;
  }
}

function saveSettings(s) {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(s));
}

function clearSettings() {
  localStorage.removeItem(SETTINGS_KEY);
}

function hasUsableSettings() {
  return loadSettings() != null;
}

// ---------- picker ----------
const TYPE_NAMES = {
  mcq_single: ["Multiple Choice", "Single correct answer"],
  reorder: ["Re-order Paragraphs", "Arrange paragraphs in logical order"],
  fib: ["Fill in the Blanks", "Pick the right word for each blank"],
  wfd: ["Write From Dictation", "Listen and type the sentence exactly"],
  swt: ["Summarize Written Text", "One sentence, 5-75 words"],
  essay: ["Write Essay", "200-300 words, structured argument"],
};

function renderPicker() {
  $("#card").classList.add("hidden");
  $("#feedback").classList.add("hidden");
  $("#tips").classList.add("hidden");
  $("#tips-view").classList.add("hidden");
  $("#settings-view").classList.add("hidden");
  $("#picker").classList.remove("hidden");
  $("#picker-title").textContent = `Pick a ${state.section} task type`;

  const types = new Set(
    state.bank.questions.filter((q) => q.section === state.section).map((q) => q.type)
  );

  const list = $("#picker-list");
  clear(list);
  for (const t of types) {
    const [name, desc] = TYPE_NAMES[t] || [t, ""];
    list.appendChild(
      el(
        "div",
        { class: "picker-item", onclick: () => pickByType(t) },
        el("div", { class: "pname" }, name),
        el("div", { class: "pdesc" }, desc)
      )
    );
  }
}

function pickByType(type) {
  const candidates = state.bank.questions.filter(
    (q) => q.section === state.section && q.type === type
  );
  const q = candidates[Math.floor(Math.random() * candidates.length)];
  renderQuestion(q);
}

function pickRandom() {
  const candidates = state.bank.questions.filter((q) => q.section === state.section);
  const q = candidates[Math.floor(Math.random() * candidates.length)];
  renderQuestion(q);
}

// ---------- render question ----------
function renderQuestion(q) {
  state.currentQ = q;
  $("#picker").classList.add("hidden");
  $("#feedback").classList.add("hidden");
  $("#bridge-status").classList.add("hidden");
  $("#tips-view").classList.add("hidden");
  $("#settings-view").classList.add("hidden");

  const card = $("#card");
  card.classList.remove("hidden");
  clear(card);

  const renderer = RENDERERS[q.type];
  if (!renderer) {
    card.appendChild(el("p", null, `Unsupported type: ${q.type}`));
    return;
  }
  renderer(card, q);
  renderTips(q.type);
}

function renderTips(type) {
  const key = `${state.section}_${type}`;
  const tips = state.bank.tips[key];
  const aside = $("#tips");
  if (!tips || !tips.length) {
    aside.classList.add("hidden");
    return;
  }
  const list = $("#tips-list");
  clear(list);
  // tips can be either array of strings (legacy) or array of {cat, tip} (new)
  const isGrouped = typeof tips[0] === "object" && tips[0] !== null;
  if (!isGrouped) {
    for (const t of tips) list.appendChild(el("li", null, t));
  } else {
    const groups = groupByCategory(tips);
    for (const [cat, items] of groups) {
      list.appendChild(el("div", { class: "cat-label" }, cat));
      const ul = el("ul", null);
      for (const item of items) ul.appendChild(el("li", null, item));
      list.appendChild(ul);
    }
  }
  aside.classList.remove("hidden");
}

function groupByCategory(tips) {
  const order = [];
  const map = new Map();
  for (const t of tips) {
    const cat = t.cat || "General";
    if (!map.has(cat)) {
      map.set(cat, []);
      order.push(cat);
    }
    map.get(cat).push(t.tip);
  }
  return order.map((c) => [c, map.get(c)]);
}

// ---------- full tips browser ----------
const TIPS_SECTION_META = {
  exam: { title: "Exam Strategy & Test Day", subtitle: "Overall scoring logic, time management, what to do on test day, and how to target your score band." },
  reading_mcq_single: { title: "Reading — Multiple Choice (Single Answer)", subtitle: "Strategy for skimming, eliminating distractors, and avoiding paraphrase traps." },
  reading_reorder: { title: "Reading — Re-order Paragraphs", subtitle: "How to find the topic sentence and sequence using connectors, pronouns, and time markers." },
  reading_fib: { title: "Reading — Fill in the Blanks", subtitle: "Collocations, grammar matching, and high-leverage scoring across Reading + Writing." },
  listening_wfd: { title: "Listening — Write From Dictation", subtitle: "The single highest-leverage task in the exam. Dual-scores Listening + Writing." },
  listening_general: { title: "Listening — Other Tasks", subtitle: "Strategy for Summarize Spoken Text, Highlight Correct Summary, Fill in Blanks, and more." },
  writing_swt: { title: "Writing — Summarize Written Text", subtitle: "One-sentence summaries: templates, grammar structures, and PTE rubric breakdown." },
  writing_essay: { title: "Writing — Essay", subtitle: "5-paragraph templates, question-type identification, and connector rotation." },
  speaking_general: { title: "Speaking — All Tasks (Real Exam)", subtitle: "Not yet practiced in PteracAI — strategy reference for Read Aloud, Repeat Sentence, Describe Image, Re-tell Lecture, and Answer Short Question." },
};

const TIPS_ORDER = [
  "exam",
  "reading_mcq_single",
  "reading_reorder",
  "reading_fib",
  "listening_wfd",
  "listening_general",
  "writing_swt",
  "writing_essay",
  "speaking_general",
];

function renderTipsView() {
  $("#picker").classList.add("hidden");
  $("#card").classList.add("hidden");
  $("#feedback").classList.add("hidden");
  $("#bridge-status").classList.add("hidden");
  $("#tips").classList.add("hidden");
  $("#settings-view").classList.add("hidden");
  state.currentFollowupOf = null;

  const view = $("#tips-view");
  view.classList.remove("hidden");
  clear(view);

  view.appendChild(el("h2", null, "PTE Tips & Strategy"));
  view.appendChild(el(
    "div",
    { class: "subtitle" },
    "High-leverage, PTE-specific guidance for each phase of the exam. Click a section below to jump."
  ));

  // table of contents
  const toc = el("div", { class: "tips-toc" });
  for (const key of TIPS_ORDER) {
    if (!state.bank.tips[key]) continue;
    const meta = TIPS_SECTION_META[key] || { title: key };
    toc.appendChild(el(
      "button",
      {
        onclick: () => document.getElementById(`tipsec-${key}`)?.scrollIntoView({ behavior: "smooth", block: "start" }),
      },
      meta.title
    ));
  }
  view.appendChild(toc);

  // sections
  for (const key of TIPS_ORDER) {
    const tips = state.bank.tips[key];
    if (!tips) continue;
    const meta = TIPS_SECTION_META[key] || { title: key, subtitle: "" };

    const section = el("section", { class: "tips-section", id: `tipsec-${key}` });
    section.appendChild(el("h3", null, meta.title));
    if (meta.subtitle) section.appendChild(el("div", { class: "section-meta" }, meta.subtitle));

    const isGrouped = typeof tips[0] === "object" && tips[0] !== null;
    if (!isGrouped) {
      const ul = el("ul", null);
      for (const t of tips) ul.appendChild(el("li", null, t));
      section.appendChild(ul);
    } else {
      const groups = groupByCategory(tips);
      for (const [cat, items] of groups) {
        const block = el("div", { class: "cat-block" });
        block.appendChild(el("div", { class: "cat-header" }, cat));
        const ul = el("ul", null);
        for (const item of items) ul.appendChild(el("li", null, item));
        block.appendChild(ul);
        section.appendChild(block);
      }
    }
    view.appendChild(section);
  }
}

const RENDERERS = {
  mcq_single(card, q) {
    card.appendChild(el("div", { class: "passage" }, q.passage));
    card.appendChild(el("div", { class: "qprompt" }, q.question));
    const opts = el("div", { class: "options" });
    let selected = -1;
    q.options.forEach((opt, idx) => {
      const o = el("div", { class: "option" }, opt);
      o.addEventListener("click", () => {
        opts.querySelectorAll(".option").forEach((x) => x.classList.remove("selected"));
        o.classList.add("selected");
        selected = idx;
      });
      opts.appendChild(o);
    });
    card.appendChild(opts);
    card.appendChild(actionsBar(() => {
      if (selected < 0) return alert("Pick one option first.");
      gradeAuto(q, selected);
    }));
  },

  reorder(card, q) {
    const order = q.paragraphs.map((_, i) => i);
    const zone = el("div", { class: "reorder-zone" });

    function repaint() {
      clear(zone);
      order.forEach((origIdx, displayIdx) => {
        const upBtn = el("button", {
          class: "ghost",
          style: "padding:2px 8px;margin-left:8px;font-size:12px;",
          onclick: () => {
            if (displayIdx === 0) return;
            [order[displayIdx - 1], order[displayIdx]] = [order[displayIdx], order[displayIdx - 1]];
            repaint();
          },
        }, "↑");
        const downBtn = el("button", {
          class: "ghost",
          style: "padding:2px 8px;margin-left:4px;font-size:12px;",
          onclick: () => {
            if (displayIdx === order.length - 1) return;
            [order[displayIdx + 1], order[displayIdx]] = [order[displayIdx], order[displayIdx + 1]];
            repaint();
          },
        }, "↓");
        const row = el(
          "div",
          { class: "reorder-item" },
          el("span", { class: "order-num" }, String(displayIdx + 1)),
          q.paragraphs[origIdx],
          upBtn,
          downBtn
        );
        zone.appendChild(row);
      });
    }
    repaint();

    card.appendChild(el("div", { class: "qprompt" }, "Arrange these paragraphs in the correct order:"));
    card.appendChild(zone);
    card.appendChild(actionsBar(() => gradeAuto(q, order.slice())));
  },

  fib(card, q) {
    card.appendChild(el("div", { class: "qprompt" }, "Choose the word that fits each blank:"));
    const wrap = el("div", { class: "fib-text" });
    const selected = new Array(q.options.length).fill(-1);
    q.text_parts.forEach((part, i) => {
      wrap.appendChild(document.createTextNode(part));
      if (i < q.options.length) {
        const sel = el("select", {
          onchange: (e) => { selected[i] = parseInt(e.target.value, 10); },
        });
        sel.appendChild(el("option", { value: "-1" }, "— choose —"));
        q.options[i].forEach((opt, idx) => {
          sel.appendChild(el("option", { value: String(idx) }, opt));
        });
        wrap.appendChild(sel);
      }
    });
    card.appendChild(wrap);
    card.appendChild(actionsBar(() => {
      if (selected.some((v) => v < 0)) return alert("Fill every blank first.");
      gradeAuto(q, selected);
    }));
  },

  wfd(card, q) {
    card.appendChild(el("div", { class: "qprompt" }, "Listen and type the sentence exactly as you hear it."));
    const controls = el("div", { class: "wfd-controls" });
    controls.appendChild(el("button", { onclick: () => speak(q.audio_text) }, "▶  Play audio"));
    controls.appendChild(el("button", { onclick: () => speak(q.audio_text, 0.7) }, "▶  Play slow"));
    card.appendChild(controls);

    const input = el("textarea", { class: "wfd-input", placeholder: "Type the sentence here..." });
    card.appendChild(input);
    card.appendChild(actionsBar(() => gradeAuto(q, input.value.trim())));

    setTimeout(() => speak(q.audio_text), 300);
  },

  swt(card, q) {
    card.appendChild(el("div", { class: "passage" }, q.passage));
    card.appendChild(el("div", { class: "qprompt" }, "Summarize the passage above in ONE sentence (5-75 words):"));
    const input = el("textarea", { class: "wfd-input", placeholder: "Write one sentence..." });
    const count = el("div", { class: "word-count" }, "0 words");
    input.addEventListener("input", () => {
      const n = countWords(input.value);
      count.textContent = `${n} words`;
      count.className = "word-count " + (n >= 5 && n <= 75 ? "ok" : "bad");
    });
    card.appendChild(input);
    card.appendChild(count);
    card.appendChild(actionsBar(() => {
      if (!input.value.trim()) return alert("Write something first.");
      submitForLLMGrading(q, input.value.trim());
    }));
  },

  essay(card, q) {
    card.appendChild(el("div", { class: "qprompt" }, q.prompt));
    const input = el("textarea", { class: "essay-input", placeholder: "Write your essay here..." });
    const count = el("div", { class: "word-count" }, "0 words");
    input.addEventListener("input", () => {
      const n = countWords(input.value);
      count.textContent = `${n} words`;
      count.className = "word-count " + (n >= 200 && n <= 300 ? "ok" : "bad");
    });
    card.appendChild(input);
    card.appendChild(count);
    card.appendChild(actionsBar(() => {
      if (countWords(input.value) < 50) return alert("Write at least a few paragraphs first.");
      submitForLLMGrading(q, input.value.trim());
    }));
  },
};

function actionsBar(onSubmit) {
  return el(
    "div",
    { class: "actions" },
    el("button", { class: "primary", onclick: onSubmit }, "Submit"),
    el("button", { class: "ghost", onclick: () => renderPicker() }, "Back")
  );
}

function countWords(s) {
  return (s.trim().match(/\S+/g) || []).length;
}

function speak(text, rate = 0.95) {
  if (!("speechSynthesis" in window)) {
    alert("Your browser doesn't support speech synthesis. Try Chrome or Safari.");
    return;
  }
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.rate = rate;
  u.pitch = 1;
  const voices = speechSynthesis.getVoices();
  const preferred = voices.find((v) => /en-(US|GB|AU)/i.test(v.lang) && /samantha|daniel|karen|google/i.test(v.name))
    || voices.find((v) => /en-(US|GB|AU)/i.test(v.lang));
  if (preferred) u.voice = preferred;
  speechSynthesis.speak(u);
}

// ---------- grading: auto ----------
function gradeAuto(q, userAnswer) {
  const correct = checkAnswer(q, userAnswer);
  recordAttempt(q, userAnswer, correct);
  showFeedback(q, userAnswer, correct);
}

function checkAnswer(q, ans) {
  if (q.type === "mcq_single") return ans === q.answer;
  if (q.type === "reorder") return JSON.stringify(ans) === JSON.stringify(q.answer);
  if (q.type === "fib") return JSON.stringify(ans) === JSON.stringify(q.answer);
  if (q.type === "wfd") {
    const norm = (s) => s.toLowerCase().replace(/[.,!?;:]/g, "").replace(/\s+/g, " ").trim();
    return norm(ans) === norm(q.answer);
  }
  return false;
}

function recordAttempt(q, userAnswer, correct) {
  state.attempted += 1;
  if (correct) {
    state.correct += 1;
    state.streak += 1;
  } else {
    state.streak = 0;
  }
  $("#stat-attempted").textContent = state.attempted;
  $("#stat-correct").textContent = state.correct;
  $("#stat-streak").textContent = state.streak;
  fetch("/api/attempt", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      qid: q.id,
      section: q.section,
      type: q.type,
      topic: q.topic,
      correct,
      user_answer: userAnswer,
      is_followup_of: state.currentFollowupOf,
    }),
  });
}

// ---------- feedback ----------
function showFeedback(q, userAnswer, correct) {
  $("#card").classList.add("hidden");
  const fb = $("#feedback");
  fb.classList.remove("hidden");
  clear(fb);

  fb.appendChild(el(
    "div",
    { class: "feedback-verdict " + (correct ? "correct" : "wrong") },
    correct ? "Correct" : "Not quite"
  ));

  if (!correct) {
    fb.appendChild(answerDisplay(q));
  }

  if (q.explanation) {
    fb.appendChild(el("div", { class: "feedback-label" }, "Why"));
    fb.appendChild(el("div", { class: "feedback-explanation" }, q.explanation));
  }
  if (!correct && q.trap) {
    fb.appendChild(el(
      "div",
      { class: "feedback-trap" },
      el("div", { class: "feedback-label" }, "Common trap"),
      q.trap
    ));
  }

  const actions = el("div", { class: "actions" });
  if (correct && state.currentFollowupOf) {
    fb.appendChild(el("div", { class: "feedback-verdict correct" }, "Mastery confirmed ✓"));
    state.currentFollowupOf = null;
    actions.appendChild(el("button", { class: "primary", onclick: () => renderPicker() }, "Next topic"));
  } else if (correct) {
    actions.appendChild(el("button", { class: "primary", onclick: () => pickByType(q.type) }, "Next question"));
    actions.appendChild(el("button", { class: "ghost", onclick: () => renderPicker() }, "Back to picker"));
  } else {
    actions.appendChild(el(
      "button",
      { class: "primary", onclick: () => requestFollowup(q) },
      "Get a similar question (mastery check)"
    ));
    actions.appendChild(el("button", { class: "ghost", onclick: () => pickByType(q.type) }, "Skip, new question"));
    actions.appendChild(el("button", { class: "ghost", onclick: () => renderPicker() }, "Back to picker"));
  }
  fb.appendChild(actions);
}

function answerDisplay(q) {
  const wrap = el("div", { class: "feedback-explanation" });
  wrap.appendChild(el("div", { class: "feedback-label" }, "Correct answer"));
  if (q.type === "mcq_single") {
    wrap.appendChild(el("div", null, q.options[q.answer]));
  } else if (q.type === "reorder") {
    const ol = el("ol", null);
    q.answer.forEach((idx) => ol.appendChild(el("li", null, q.paragraphs[idx])));
    wrap.appendChild(ol);
  } else if (q.type === "fib") {
    wrap.appendChild(el("div", null, q.answer.map((idx, i) => q.options[i][idx]).join("  /  ")));
  } else if (q.type === "wfd") {
    wrap.appendChild(el("div", { class: "passage" }, q.answer));
  } else {
    wrap.appendChild(el("div", null, JSON.stringify(q.answer)));
  }
  return wrap;
}

// ---------- bridge: follow-up & LLM grading ----------
function requestFollowup(q) {
  state.currentFollowupOf = q.id;
  const request = {
    kind: "followup",
    original_qid: q.id,
    section: q.section,
    type: q.type,
    topic: q.topic,
    notes: "User got this wrong. Generate ONE new question of the same type and topic that tests the same skill. Reply as a single JSON object matching the bank.json question schema.",
    original_question: q,
  };
  postRequest(request, (resp) => {
    if (resp.question) {
      renderQuestion(resp.question);
    } else if (resp.error) {
      alert("Claude Code reported: " + resp.error);
    }
  });
}

function submitForLLMGrading(q, userAnswer) {
  const request = {
    kind: "grade",
    qid: q.id,
    section: q.section,
    type: q.type,
    question: q,
    user_answer: userAnswer,
    notes: "Grade this against the PTE rubric. Reply with JSON: {correct: bool, score: '0-3' or similar, explanation: '...', improvements: ['...']}.",
  };
  postRequest(request, (resp) => {
    if (resp.grading) {
      showLLMGrading(q, userAnswer, resp.grading);
    } else if (resp.error) {
      alert("Claude Code reported: " + resp.error);
    }
  });
}

function showLLMGrading(q, userAnswer, g) {
  const correct = !!g.correct;
  recordAttempt(q, userAnswer, correct);
  $("#card").classList.add("hidden");
  const fb = $("#feedback");
  fb.classList.remove("hidden");
  clear(fb);
  fb.appendChild(el(
    "div",
    { class: "feedback-verdict " + (correct ? "correct" : "wrong") },
    correct ? "Strong response" : "Needs work"
  ));
  if (g.score != null) {
    fb.appendChild(el("div", { class: "feedback-label" }, "Score"));
    fb.appendChild(el("div", { class: "feedback-explanation" }, String(g.score)));
  }
  if (g.explanation) {
    fb.appendChild(el("div", { class: "feedback-label" }, "Feedback"));
    fb.appendChild(el("div", { class: "feedback-explanation" }, g.explanation));
  }
  if (Array.isArray(g.improvements) && g.improvements.length) {
    fb.appendChild(el("div", { class: "feedback-label" }, "Improvements"));
    const ul = el("ul", null);
    g.improvements.forEach((s) => ul.appendChild(el("li", null, s)));
    fb.appendChild(ul);
  }
  const actions = el("div", { class: "actions" });
  if (!correct) {
    actions.appendChild(el(
      "button",
      { class: "primary", onclick: () => requestFollowup(q) },
      "Try a similar prompt (mastery check)"
    ));
  }
  actions.appendChild(el("button", { class: "primary", onclick: () => pickByType(q.type) }, "Next question"));
  actions.appendChild(el("button", { class: "ghost", onclick: () => renderPicker() }, "Back to picker"));
  fb.appendChild(actions);
}

async function postRequest(request, handler) {
  // BYOK mode (Vercel): include the visitor's stored API key headers.
  // If no key is configured, prompt to set one before making the call.
  const settings = loadSettings();
  const headers = { "Content-Type": "application/json" };
  if (settings) {
    headers["x-provider"] = settings.provider;
    headers["x-api-key"] = settings.apiKey;
    if (settings.model) headers["x-model"] = settings.model;
  } else {
    // Allow local file-bridge mode without key (Claude Code in terminal handles it).
    // But on the deployed site without a key, surface a friendly prompt.
    const wantsConfig = confirm(
      "This action needs an AI provider key.\n\n" +
      "If you're running PteracAI locally with Claude Code in your terminal, you can ignore this.\n\n" +
      "Otherwise click OK to open Settings and configure your key (Anthropic / OpenAI / OpenRouter)."
    );
    if (wantsConfig) {
      $("#settings-nav").click();
      return;
    }
  }

  showBridgeStatus(true);
  let res;
  try {
    res = await fetch("/api/request", {
      method: "POST",
      headers,
      body: JSON.stringify(request),
    });
  } catch (e) {
    showBridgeStatus(false);
    alert("Network error: " + e.message);
    return;
  }

  if (!res.ok) {
    showBridgeStatus(false);
    let msg = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (body?.error) msg = body.error;
    } catch (_) {}
    alert("Request failed: " + msg);
    return;
  }

  const body = await res.json();

  // Vercel mode: response contains the full payload synchronously.
  if (body.question || body.grading) {
    showBridgeStatus(false);
    handler(body);
    return;
  }

  // Local file-bridge mode: response acknowledges with an id; poll for the result.
  if (body.id) {
    state.inflightById.set(body.id, handler);
    return;
  }

  showBridgeStatus(false);
  alert("Unexpected response from /api/request.");
}

function showBridgeStatus(visible) {
  $("#bridge-status").classList.toggle("hidden", !visible);
  const hint = $("#bridge-hint");
  if (!visible) {
    if (state.bridgeHintTimer) clearTimeout(state.bridgeHintTimer);
    hint.classList.add("hidden");
    return;
  }
  hint.classList.add("hidden");
  state.bridgeHintTimer = setTimeout(() => {
    if (!$("#bridge-status").classList.contains("hidden")) {
      hint.classList.remove("hidden");
    }
  }, 3000);
}

// ---------- polling ----------
function startPolling() {
  if (state.pollTimer) return;
  state.pollTimer = setInterval(pollResponses, 1500);
}

async function pollResponses() {
  if (state.inflightById.size === 0) return;
  try {
    const res = await fetch(`/api/responses?since=${state.responseSeq}`);
    const { responses } = await res.json();
    for (const r of responses) {
      state.responseSeq = Math.max(state.responseSeq, r.seq || 0);
      const handler = state.inflightById.get(r.request_id);
      if (handler) {
        state.inflightById.delete(r.request_id);
        handler(r);
      }
    }
    if (state.inflightById.size === 0) showBridgeStatus(false);
  } catch (e) {
    // server might be restarting; just try again
  }
}

// ---------- settings view (BYOK) ----------
function renderSettingsView() {
  $("#picker").classList.add("hidden");
  $("#card").classList.add("hidden");
  $("#feedback").classList.add("hidden");
  $("#bridge-status").classList.add("hidden");
  $("#tips").classList.add("hidden");
  $("#tips-view").classList.add("hidden");

  const view = $("#settings-view");
  view.classList.remove("hidden");
  clear(view);

  view.appendChild(el("h2", null, "Settings — Bring Your Own AI Key"));
  view.appendChild(el(
    "div",
    { class: "subtitle" },
    "PteracAI is free to use. You bring your own API key from the provider of your choice. Your key is stored only in this browser and is never logged on the server."
  ));

  const current = loadSettings();
  const initialProvider = current?.provider || "anthropic";

  // Provider row
  const providerRow = el("div", { class: "settings-row" });
  providerRow.appendChild(el("label", { for: "set-provider" }, "Provider"));
  const providerSelect = el("select", { id: "set-provider" });
  for (const [id, p] of Object.entries(PROVIDERS)) {
    const opt = el("option", { value: id }, p.label);
    if (id === initialProvider) opt.setAttribute("selected", "");
    providerSelect.appendChild(opt);
  }
  providerRow.appendChild(providerSelect);
  view.appendChild(providerRow);

  // Get-key link (updates with provider change)
  const linkRow = el("div", { class: "settings-link" });
  function refreshLinkRow() {
    clear(linkRow);
    const p = PROVIDERS[providerSelect.value];
    linkRow.appendChild(document.createTextNode("Don't have a key? Get one at "));
    const a = el("a", { href: p.getKeyUrl, target: "_blank", rel: "noopener" }, p.getKeyUrl);
    linkRow.appendChild(a);
    linkRow.appendChild(document.createTextNode(` (${p.keyHint})`));
  }
  refreshLinkRow();
  view.appendChild(linkRow);

  // Key row
  const keyRow = el("div", { class: "settings-row", style: "margin-top: 18px;" });
  keyRow.appendChild(el("label", { for: "set-key" }, "API Key"));
  const keyWrap = el("div", { class: "settings-key-wrap" });
  const keyInput = el("input", {
    id: "set-key",
    type: "password",
    placeholder: "Paste your API key here",
    autocomplete: "off",
    spellcheck: "false",
    value: current?.apiKey || "",
  });
  const showBtn = el("button", { type: "button" }, "Show");
  showBtn.addEventListener("click", () => {
    const showing = keyInput.type === "text";
    keyInput.type = showing ? "password" : "text";
    showBtn.textContent = showing ? "Show" : "Hide";
  });
  keyWrap.appendChild(keyInput);
  keyWrap.appendChild(showBtn);
  keyRow.appendChild(keyWrap);
  view.appendChild(keyRow);

  // Model row
  const modelRow = el("div", { class: "settings-row" });
  modelRow.appendChild(el("label", { for: "set-model" }, "Model"));
  const modelSelect = el("select", { id: "set-model" });
  function refreshModels() {
    clear(modelSelect);
    const p = PROVIDERS[providerSelect.value];
    for (const m of p.models) {
      const opt = el("option", { value: m.id }, m.label);
      if (current && current.provider === providerSelect.value && current.model === m.id) {
        opt.setAttribute("selected", "");
      }
      modelSelect.appendChild(opt);
    }
  }
  refreshModels();
  modelRow.appendChild(modelSelect);
  view.appendChild(modelRow);

  providerSelect.addEventListener("change", () => {
    refreshModels();
    refreshLinkRow();
  });

  // Status banner
  const status = el("div", { id: "set-status", class: "settings-status" });
  view.appendChild(status);

  // Actions
  const actions = el("div", { class: "settings-actions" });
  const saveBtn = el("button", { class: "primary" }, "Save");
  const testBtn = el("button", { class: "ghost" }, "Test connection");
  const clearBtn = el("button", { class: "ghost" }, "Clear stored key");
  actions.appendChild(saveBtn);
  actions.appendChild(testBtn);
  actions.appendChild(clearBtn);
  view.appendChild(actions);

  saveBtn.addEventListener("click", () => {
    if (!keyInput.value.trim()) return setStatus("err", "Paste your API key first.");
    saveSettings({
      provider: providerSelect.value,
      apiKey: keyInput.value.trim(),
      model: modelSelect.value,
    });
    setStatus("ok", "Saved to this browser. Try a Writing prompt or click 'Get a similar question' on a wrong answer to test the loop.");
  });

  testBtn.addEventListener("click", async () => {
    if (!keyInput.value.trim()) return setStatus("err", "Paste your API key first.");
    setStatus("info", "Testing connection... (sending a minimal grading request)");
    const probe = {
      kind: "grade",
      type: "swt",
      question: { type: "swt", topic: "test", passage: "The sky is blue.", rubric: "", sample: "", grading_notes: "" },
      user_answer: "The sky appears blue.",
    };
    try {
      const res = await fetch("/api/request", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-provider": providerSelect.value,
          "x-api-key": keyInput.value.trim(),
          "x-model": modelSelect.value,
        },
        body: JSON.stringify(probe),
      });
      const body = await res.json().catch(() => ({}));
      if (res.ok && (body.grading || body.question)) {
        setStatus("ok", "Connection works. The provider replied successfully.");
      } else {
        setStatus("err", `Test failed (HTTP ${res.status}): ${body.error || "unknown error"}`);
      }
    } catch (e) {
      setStatus("err", "Network error: " + e.message);
    }
  });

  clearBtn.addEventListener("click", () => {
    if (!confirm("Clear your stored API key from this browser?")) return;
    clearSettings();
    keyInput.value = "";
    setStatus("info", "Cleared. The site won't make any LLM calls until you save a new key.");
  });

  // Privacy disclosure
  const privacy = el("div", { class: "settings-privacy" });
  privacy.appendChild(el("h4", null, "How your key is handled"));
  privacy.appendChild(el(
    "div",
    null,
    "Your API key is stored in this browser's localStorage — it never leaves your device except as an HTTPS header when you submit a writing task or request a follow-up question. The serverless function at /api/request forwards your request to the provider you selected using your key, then returns the result. The key is NOT logged, persisted, or sent anywhere else."
  ));
  const sourceLink = el("div", { style: "margin-top: 10px;" });
  sourceLink.appendChild(document.createTextNode("Verify in the source: "));
  sourceLink.appendChild(el("a", { href: REPO_URL + "/blob/main/api/request.js", target: "_blank", rel: "noopener" }, "api/request.js"));
  privacy.appendChild(sourceLink);
  view.appendChild(privacy);

  function setStatus(kind, msg) {
    status.className = "settings-status show " + kind;
    status.textContent = msg;
  }
}

boot();
