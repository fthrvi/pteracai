// PteracAI — frontend logic
// Architecture: vanilla JS, no framework. Loads bank.json, renders one
// question at a time, grades auto-gradable types client-side, posts
// LLM-grading and follow-up requests to the local server, then polls
// /api/responses for Claude Code's reply.

// ---------- BUILD CONFIG ----------
// To enable Google Drive sync (cross-device progress), create an OAuth
// 2.0 Client ID in Google Cloud Console with the
// https://www.googleapis.com/auth/drive.appdata scope, then paste it here
// or set it on window.PTERACAI_GOOGLE_CLIENT_ID before this script loads.
// See README → "Google Sign-In setup" for the 3-minute walkthrough.
const GOOGLE_CLIENT_ID = window.PTERACAI_GOOGLE_CLIENT_ID || "";

const TEST_KEY = "pteracai_test_v1";
const TEST_LABELS = {
  pte: { label: "PTE Academic", short: "PTE", available: true },
  ielts: { label: "IELTS Academic", short: "IELTS", available: true },
  toefl: { label: "TOEFL iBT", short: "TOEFL", available: false },
  duolingo: { label: "Duolingo English Test", short: "Duolingo", available: false },
};

function loadCurrentTest() {
  const stored = localStorage.getItem(TEST_KEY);
  if (stored && TEST_LABELS[stored]?.available) return stored;
  return "pte";
}

function saveCurrentTest(t) {
  localStorage.setItem(TEST_KEY, t);
}

const state = {
  bank: null,
  test: loadCurrentTest(),
  section: "reading",
  currentQ: null,
  currentFollowupOf: null,
  attempted: 0,
  correct: 0,
  streak: 0,
  responseSeq: 0,
  pollTimer: null,
  inflightById: new Map(),
  pendingCoaching: null,
  keyHandler: null,
  freeTierAvailable: false,
  mockExam: null, // {active, test, section, queue, index, startTs, durationSec, results}
};

// Mock exam configurations — section, item count, total duration. Reflects
// official PTE/IELTS section timings (approximated for the local question set).
const MOCK_CONFIGS = {
  pte: {
    reading: { label: "Reading", durationSec: 30 * 60, count: 12 },
    listening: { label: "Listening", durationSec: 35 * 60, count: 10 },
    writing: { label: "Writing", durationSec: 25 * 60, count: 2 },
    speaking: { label: "Speaking", durationSec: 30 * 60, count: 8 },
  },
  ielts: {
    reading: { label: "Reading", durationSec: 60 * 60, count: 15 },
    listening: { label: "Listening", durationSec: 30 * 60, count: 10 },
    writing: { label: "Writing", durationSec: 60 * 60, count: 2 },
    speaking: { label: "Speaking", durationSec: 14 * 60, count: 5 },
  },
};

const FREE_TIER_QUOTA = 20; // requests per day per visitor
const FREE_TIER_USAGE_KEY = "pteracai_free_tier_usage_v1";

function todayKey() {
  return new Date().toISOString().slice(0, 10); // YYYY-MM-DD
}

function getFreeTierUsageToday() {
  try {
    const data = JSON.parse(localStorage.getItem(FREE_TIER_USAGE_KEY) || "{}");
    return data.date === todayKey() ? (data.count || 0) : 0;
  } catch {
    return 0;
  }
}

function incrementFreeTierUsage() {
  const count = getFreeTierUsageToday() + 1;
  localStorage.setItem(FREE_TIER_USAGE_KEY, JSON.stringify({ date: todayKey(), count }));
  return count;
}

function freeTierRemaining() {
  return Math.max(0, FREE_TIER_QUOTA - getFreeTierUsageToday());
}

function freeTierUsable() {
  return state.freeTierAvailable && freeTierRemaining() > 0;
}

// AI is "available" if user has own key OR free tier is usable.
// Use this for gating LLM-dependent UI features.
function aiAvailable() {
  return loadSettings() != null || freeTierUsable();
}

function updateFreeTierBadge() {
  const badge = $("#free-tier-badge");
  if (!badge) return;
  const visible = state.freeTierAvailable && !loadSettings();
  badge.classList.toggle("hidden", !visible);
  if (!visible) return;
  const left = freeTierRemaining();
  $("#free-tier-remaining").textContent = `${left}/${FREE_TIER_QUOTA}`;
  badge.classList.toggle("low", left > 0 && left <= 5);
  badge.classList.toggle("empty", left === 0);
}

// Single global keyboard listener that delegates to state.keyHandler
window.addEventListener("keydown", (e) => {
  if (state.keyHandler) state.keyHandler(e);
});

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

// ---------- multi-test helpers ----------
function currentBank() {
  if (state.bank?.schema === 2) {
    return state.bank.tests[state.test] || state.bank.tests.pte;
  }
  // v1 fallback shouldn't happen post-migration, but keep code safe
  return { questions: state.bank?.questions || [], tips: state.bank?.tips || {} };
}

function currentQuestions() { return currentBank().questions || []; }
function currentTips() { return currentBank().tips || {}; }

// ---------- bootstrap ----------
async function boot() {
  const res = await fetch("/data/bank.json");
  state.bank = await res.json();
  // Probe the API endpoint to learn whether the shared free tier is configured.
  try {
    const probe = await fetch("/api/request").then((r) => r.json()).catch(() => null);
    if (probe?.free_tier_available) state.freeTierAvailable = true;
  } catch (_) {
    /* offline / local dev — no problem */
  }
  bindSectionButtons();
  bindLanding();
  startPolling();
  initSync();
  showAppropriateInitialView();
}

const SKIP_LOGIN_KEY = "pteracai_skip_login_v1";

function bindLanding() {
  const btn = $("#landing-signin");
  if (btn) {
    btn.addEventListener("click", async () => {
      const err = $("#landing-error");
      err.classList.add("hidden");
      btn.disabled = true;
      btn.textContent = "Opening Google sign-in...";
      try {
        if (!window.PteracaiSync || !PteracaiSync.configured()) {
          throw new Error("Sync is not configured. Set window.PTERACAI_GOOGLE_CLIENT_ID.");
        }
        await PteracaiSync.signIn();
        // signing in clears the skip flag — they opted into sync
        localStorage.removeItem(SKIP_LOGIN_KEY);
        // onSignInChange will call showMainApp
      } catch (e) {
        err.textContent = "Sign-in failed: " + (e.message || "unknown error");
        err.classList.remove("hidden");
        btn.disabled = false;
        btn.textContent = "Sign in with Google to start";
      }
    });
  }
  const skip = $("#landing-skip");
  if (skip) {
    skip.addEventListener("click", (e) => {
      e.preventDefault();
      localStorage.setItem(SKIP_LOGIN_KEY, "1");
      showMainApp();
    });
  }
}

function showAppropriateInitialView() {
  const syncReady = window.PteracaiSync && PteracaiSync.configured();
  const skipped = localStorage.getItem(SKIP_LOGIN_KEY) === "1";
  if (syncReady && !PteracaiSync.signedIn() && !skipped) {
    showLanding();
  } else {
    showMainApp();
  }
}

function showLanding() {
  $("#landing-view").classList.remove("hidden");
  $("#main-header").classList.add("hidden");
  $("#main-content").classList.add("hidden");
}

function showMainApp() {
  $("#landing-view").classList.add("hidden");
  $("#main-header").classList.remove("hidden");
  $("#main-content").classList.remove("hidden");
  updateFreeTierBadge();
  // Dashboard is the new default landing view — Home tab is active by default
  $$(".section-btn").forEach((x) => x.classList.remove("active"));
  $("#home-nav").classList.add("active");
  renderDashboardView();
}

function initSync() {
  if (!window.PteracaiSync) return;
  PteracaiSync.init({
    clientId: GOOGLE_CLIENT_ID,
    onSignInChange: async ({ signedIn, user, source }) => {
      if (signedIn) {
        await pullAndMerge();
        // First time signing in OR cached session resume → show the app
        showMainApp();
        // Re-render Settings panel if visible so user sees their state
        if (!$("#settings-view").classList.contains("hidden")) {
          renderSettingsView();
        }
      } else {
        // signed out → back to landing (only if sync is configured)
        if (PteracaiSync.configured()) {
          showLanding();
        }
        if (!$("#settings-view").classList.contains("hidden")) {
          renderSettingsView();
        }
      }
    },
  });
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
  $("#home-nav").addEventListener("click", () => {
    $$(".section-btn").forEach((x) => x.classList.remove("active"));
    $("#home-nav").classList.add("active");
    renderDashboardView();
  });
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
  bindTestPill();
}

function bindTestPill() {
  const pill = $("#test-pill");
  const menu = $("#test-pill-menu");
  const label = $("#test-pill-label");
  label.textContent = TEST_LABELS[state.test]?.short || "PTE";

  function openMenu() {
    clear(menu);
    for (const [id, info] of Object.entries(TEST_LABELS)) {
      const opt = el(
        "div",
        {
          class: "test-pill-option" + (id === state.test ? " active" : "") + (info.available ? "" : " disabled"),
          role: "option",
        },
        el("span", { class: "test-pill-dot" }),
        info.label,
        info.available ? null : el("span", { class: "test-pill-meta" }, "soon")
      );
      if (info.available && id !== state.test) {
        opt.addEventListener("click", () => {
          state.test = id;
          saveCurrentTest(id);
          label.textContent = info.short;
          closeMenu();
          state.section = "reading";
          $$(".section-btn[data-section]").forEach((b) => b.classList.toggle("active", b.dataset.section === "reading"));
          renderPicker();
        });
      }
      menu.appendChild(opt);
    }
    menu.classList.remove("hidden");
    setTimeout(() => document.addEventListener("click", outsideClick), 0);
  }
  function closeMenu() {
    menu.classList.add("hidden");
    document.removeEventListener("click", outsideClick);
  }
  function outsideClick(e) {
    if (!menu.contains(e.target) && !pill.contains(e.target)) closeMenu();
  }
  pill.addEventListener("click", (e) => {
    e.stopPropagation();
    menu.classList.contains("hidden") ? openMenu() : closeMenu();
  });
  pill.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      pill.click();
    }
  });
}

// ---------- BYOK settings (localStorage) ----------
const SETTINGS_KEY = "pteracai_settings_v1";
const REPO_URL = "https://github.com/fthrvi/pteracai";

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
  localStorage.setItem("pteracai_settings_updated", String(Date.now()));
  scheduleSyncPush();
}

function clearSettings() {
  localStorage.removeItem(SETTINGS_KEY);
}

function hasUsableSettings() {
  return loadSettings() != null;
}

// ---------- Score profile (PDF upload + LLM-generated improvement plan) ----------
const SCORE_PROFILE_KEY = "pteracai_score_profile_v1";

function loadScoreProfile() {
  try {
    const raw = localStorage.getItem(SCORE_PROFILE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function saveScoreProfile(profile) {
  localStorage.setItem(SCORE_PROFILE_KEY, JSON.stringify({
    ...profile,
    updated_at: new Date().toISOString(),
  }));
  scheduleSyncPush();
}

function clearScoreProfile() {
  localStorage.removeItem(SCORE_PROFILE_KEY);
  scheduleSyncPush();
}

// Extract text from an uploaded PDF using pdf.js (loaded via index.html).
async function extractTextFromPDF(file) {
  if (!window.PteracaiPdf) throw new Error("PDF parser not loaded yet — try again in a moment.");
  const buffer = await file.arrayBuffer();
  const pdf = await window.PteracaiPdf.getDocument({ data: buffer }).promise;
  const parts = [];
  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i);
    const content = await page.getTextContent();
    parts.push(content.items.map((it) => it.str).join(" "));
  }
  return parts.join("\n\n");
}

// ---------- progress (attempts + spaced repetition) ----------
const PROGRESS_KEY = "pteracai_progress_v1";
const MAX_ATTEMPTS_RETAINED = 1000;

function loadProgress() {
  try {
    const raw = localStorage.getItem(PROGRESS_KEY);
    if (!raw) return defaultProgress();
    const p = JSON.parse(raw);
    return { ...defaultProgress(), ...p };
  } catch (e) {
    return defaultProgress();
  }
}

function defaultProgress() {
  return {
    schema_version: 1,
    attempts: [],
    attempts_updated: 0,
    spaced_rep: {},
    spaced_rep_updated: 0,
    streaks: {}, // {topicKey: {wrong_in_a_row, last_ts}}
    streaks_updated: 0,
  };
}

function saveProgress(p) {
  localStorage.setItem(PROGRESS_KEY, JSON.stringify(p));
  scheduleSyncPush();
}

function appendAttempt(attempt) {
  const p = loadProgress();
  p.attempts.push(attempt);
  // sliding window
  if (p.attempts.length > MAX_ATTEMPTS_RETAINED) {
    p.attempts = p.attempts.slice(-MAX_ATTEMPTS_RETAINED);
  }
  p.attempts_updated = Date.now();
  // update streak for this topic
  const key = `${attempt.section}:${attempt.type}:${attempt.topic || ''}`;
  const cur = p.streaks[key] || { wrong_in_a_row: 0, last_ts: 0 };
  if (attempt.correct) {
    cur.wrong_in_a_row = 0;
  } else {
    cur.wrong_in_a_row += 1;
  }
  cur.last_ts = attempt.ts;
  p.streaks[key] = cur;
  p.streaks_updated = Date.now();
  // spaced repetition: only mark new entries; details handled elsewhere
  if (!attempt.correct) {
    p.spaced_rep[attempt.qid] = scheduleSR(p.spaced_rep[attempt.qid], false);
  } else if (p.spaced_rep[attempt.qid]) {
    p.spaced_rep[attempt.qid] = scheduleSR(p.spaced_rep[attempt.qid], true);
  }
  p.spaced_rep_updated = Date.now();
  saveProgress(p);
  return cur;
}

// SM-2-lite: intervals double on correct, reset on wrong
function scheduleSR(prev, correct) {
  const now = Date.now();
  const day = 24 * 3600 * 1000;
  if (!prev) {
    return { interval_days: 1, next_due_ts: now + day, repetitions: correct ? 1 : 0, ease: 2.5 };
  }
  if (correct) {
    const newInt = Math.round(prev.interval_days * prev.ease);
    return { interval_days: newInt, next_due_ts: now + newInt * day, repetitions: prev.repetitions + 1, ease: prev.ease };
  }
  return { interval_days: 1, next_due_ts: now + day, repetitions: 0, ease: Math.max(1.3, prev.ease - 0.2) };
}

function bumpStreakChip() {
  const chip = $("#stat-streak-chip");
  if (!chip) return;
  chip.classList.toggle("active", state.streak > 0);
  chip.classList.remove("bump");
  // force reflow then re-add for animation restart
  void chip.offsetWidth;
  chip.classList.add("bump");
  setTimeout(() => chip.classList.remove("bump"), 220);
}

function dueQuestionIds() {
  const p = loadProgress();
  const now = Date.now();
  return Object.entries(p.spaced_rep)
    .filter(([_, sr]) => sr.next_due_ts <= now)
    .map(([qid, _]) => qid);
}

// ---------- sync (Google Drive) ----------
function scheduleSyncPush() {
  if (!window.PteracaiSync?.signedIn?.()) return;
  PteracaiSync.schedulePush(() => ({
    schema_version: 1,
    settings: loadSettings(),
    settings_updated: Number(localStorage.getItem("pteracai_settings_updated") || 0),
    progress: loadProgress(),
  }));
}

async function pullAndMerge() {
  if (!window.PteracaiSync?.signedIn?.()) return;
  try {
    const remote = await PteracaiSync.pull();
    if (!remote) return; // no remote file yet, nothing to merge
    // Merge settings: take most recent by timestamp
    const localSettingsUpdated = Number(localStorage.getItem("pteracai_settings_updated") || 0);
    if (remote.settings && (remote.settings_updated || 0) > localSettingsUpdated) {
      saveSettings(remote.settings);
      localStorage.setItem("pteracai_settings_updated", String(remote.settings_updated));
    }
    // Merge progress: per-section most-recent wins; attempts merged by ts (union)
    if (remote.progress) {
      const local = loadProgress();
      const merged = { ...local };
      if ((remote.progress.attempts_updated || 0) > local.attempts_updated) {
        // union attempts by ts+qid
        const seen = new Set(local.attempts.map((a) => `${a.ts}:${a.qid}`));
        const incoming = (remote.progress.attempts || []).filter((a) => !seen.has(`${a.ts}:${a.qid}`));
        merged.attempts = [...local.attempts, ...incoming]
          .sort((a, b) => a.ts - b.ts)
          .slice(-MAX_ATTEMPTS_RETAINED);
        merged.attempts_updated = remote.progress.attempts_updated;
      }
      if ((remote.progress.spaced_rep_updated || 0) > local.spaced_rep_updated) {
        merged.spaced_rep = { ...local.spaced_rep, ...remote.progress.spaced_rep };
        merged.spaced_rep_updated = remote.progress.spaced_rep_updated;
      }
      if ((remote.progress.streaks_updated || 0) > local.streaks_updated) {
        merged.streaks = { ...local.streaks, ...remote.progress.streaks };
        merged.streaks_updated = remote.progress.streaks_updated;
      }
      localStorage.setItem(PROGRESS_KEY, JSON.stringify(merged));
    }
  } catch (e) {
    console.warn("[sync] pull failed:", e.message);
  }
}

// ---------- picker ----------
const TYPE_NAMES = {
  mcq_single: ["Multiple Choice", "Single correct answer"],
  reorder: ["Re-order Paragraphs", "Arrange paragraphs in logical order"],
  fib: ["Fill in the Blanks", "Pick the right word for each blank"],
  wfd: ["Write From Dictation", "Listen and type the sentence exactly"],
  swt: ["Summarize Written Text", "One sentence, 5-75 words"],
  essay: ["Write Essay", "200-300 words, structured argument"],
  // IELTS-specific
  tfng: ["True / False / Not Given", "Decide if a statement matches the passage"],
  task1: ["Writing Task 1", "150-word description of a chart, graph, or process"],
  matching_headings: ["Matching Headings", "Match each paragraph to the best heading"],
  // PTE Speaking
  read_aloud: ["Read Aloud", "Read the passage aloud — natural pace, clear pronunciation"],
  repeat_sentence: ["Repeat Sentence", "Listen and repeat the sentence exactly"],
  describe_image: ["Describe Image", "Speak for 25 seconds about the prompt"],
  retell_lecture: ["Re-tell Lecture", "Listen to a mini-lecture, then re-tell it in 40 seconds"],
  answer_short: ["Answer Short Question", "One-word or short-phrase answer"],
  // IELTS Speaking
  ielts_part1: ["IELTS Part 1 — Familiar Topic", "Answer in 2-3 sentences with a personal example"],
  ielts_part2: ["IELTS Part 2 — Cue Card", "1 min prep, then 1-2 min monologue covering all bullets"],
  ielts_part3: ["IELTS Part 3 — Discussion", "Abstract question, give opinion + example + nuance"],
  // Listening expansions
  lst_mcq: ["Listening Multiple Choice", "Listen to a passage, answer one MCQ"],
  lst_summary: ["Summarize Spoken Text", "Listen to a lecture, write a 50-70 word summary"],
  lst_sc: ["Listening Sentence Completion", "Listen and fill in the blanks in a printed sentence"],
};

function renderPicker() {
  $("#card").classList.add("hidden");
  $("#feedback").classList.add("hidden");
  $("#tips").classList.add("hidden");
  $("#tips-view").classList.add("hidden");
  $("#settings-view").classList.add("hidden");
  $("#dashboard-view").classList.add("hidden");
  $("#picker").classList.remove("hidden");

  const picker = $("#picker");
  clear(picker);

  const sectionLabel = state.section.charAt(0).toUpperCase() + state.section.slice(1);
  picker.appendChild(el("h2", { id: "picker-title" }, `Pick a ${state.section} task type`));

  // Per-section tips (top 3 from any category, plus link to full Tips)
  const sectionTips = collectSectionTips(state.section);
  if (sectionTips.length) {
    const tipsBox = el("div", { class: "section-tips" });
    tipsBox.appendChild(el("div", { class: "section-tips-header" },
      el("span", null, `${sectionLabel} strategy notes`),
      el("a", {
        href: "#",
        class: "section-tips-link",
        onclick: (e) => { e.preventDefault(); $("#tips-nav").click(); },
      }, "See all tips →"),
    ));
    const ul = el("ul", null);
    sectionTips.slice(0, 4).forEach((t) => ul.appendChild(el("li", null, t)));
    tipsBox.appendChild(ul);
    picker.appendChild(tipsBox);
  }

  // Task type grid
  const types = new Set(
    currentQuestions().filter((q) => q.section === state.section).map((q) => q.type)
  );
  // Indicate that community questions blend in
  const communityNote = el(
    "div",
    { class: "picker-community-note" },
    "Questions from the seed bank are mixed with AI-generated questions contributed by other learners."
  );
  picker.appendChild(communityNote);

  const list = el("div", { id: "picker-list", class: "picker-list" });
  if (types.size === 0) {
    list.appendChild(el("div", { class: "picker-empty" },
      el("div", { class: "picker-empty-mark" }, "—"),
      el("div", { class: "picker-empty-title" }, `No ${state.section} questions yet for ${TEST_LABELS[state.test]?.short || "this test"}`),
      el("div", { class: "picker-empty-sub" }, "Content for this section is coming soon. Try a different section or switch tests via the pill in the top-left.")
    ));
  } else {
    for (const t of types) {
      const [name, desc] = TYPE_NAMES[t] || [t, ""];
      const count = currentQuestions().filter((q) => q.section === state.section && q.type === t).length;
      list.appendChild(
        el(
          "div",
          { class: "picker-item", onclick: () => pickByType(t) },
          el("div", { class: "picker-item-row" },
            el("div", { class: "pname" }, name),
            el("div", { class: "picker-count" }, `${count}`),
          ),
          el("div", { class: "pdesc" }, desc)
        )
      );
    }
  }
  picker.appendChild(list);

  if (types.size > 0) {
    const randomBtn = el("button", { id: "random-btn", class: "primary", onclick: () => pickRandom() }, "Random question");
    picker.appendChild(randomBtn);
  }
}

// Collect top per-section tips (best-of-section from the tips structure).
// Strategy: pick first 'Strategy' or 'Tricks' tip from each task-type sub-section.
function collectSectionTips(section) {
  const tips = currentTips();
  const out = [];
  for (const [key, items] of Object.entries(tips)) {
    if (!key.startsWith(section + "_")) continue;
    const arr = Array.isArray(items) ? items : [];
    // Prefer Strategy or Tricks categories first
    const strategy = arr.find((t) => t && typeof t === "object" && (t.cat === "Strategy" || t.cat === "Tricks"));
    if (strategy) out.push(strategy.tip || strategy);
    else if (arr[0]) out.push(typeof arr[0] === "string" ? arr[0] : arr[0].tip);
  }
  return out;
}

async function pickByType(type) {
  const seedCandidates = currentQuestions().filter(
    (q) => q.section === state.section && q.type === type
  );
  // Pull community questions of the same type in parallel — graceful fallback if empty
  const community = await fetchCommunityQuestions(state.test, state.section, type, 30);
  const candidates = [...seedCandidates, ...community];
  if (!candidates.length) return alert("No questions available for this type yet.");
  const q = candidates[Math.floor(Math.random() * candidates.length)];
  renderQuestion(q);
}

async function pickRandom() {
  const seedCandidates = currentQuestions().filter((q) => q.section === state.section);
  // Group community pulls by type to keep request count small
  const types = [...new Set(seedCandidates.map((q) => q.type))];
  const community = (await Promise.all(
    types.map((t) => fetchCommunityQuestions(state.test, state.section, t, 10))
  )).flat();
  const candidates = [...seedCandidates, ...community];
  if (!candidates.length) return alert("No questions available for this section yet.");
  const q = candidates[Math.floor(Math.random() * candidates.length)];
  renderQuestion(q);
}

// ---------- community bank fetching ----------
const COMMUNITY_CACHE = new Map(); // key=test:section:type → questions[]
const COMMUNITY_CACHE_TTL_MS = 5 * 60 * 1000;

async function fetchCommunityQuestions(test, section, type, limit = 30) {
  const key = `${test}:${section}:${type}`;
  const cached = COMMUNITY_CACHE.get(key);
  if (cached && Date.now() - cached.ts < COMMUNITY_CACHE_TTL_MS) {
    return cached.questions;
  }
  try {
    const url = `/api/community?test=${test}&section=${section}&type=${type}&limit=${limit}`;
    const r = await fetch(url);
    if (!r.ok) return [];
    const body = await r.json();
    const questions = body.questions || [];
    COMMUNITY_CACHE.set(key, { ts: Date.now(), questions });
    return questions;
  } catch (e) {
    return [];
  }
}

// ---------- render question ----------
function renderQuestion(q) {
  state.currentQ = q;
  state.keyHandler = null; // cleared per-render; renderers can install their own
  $("#picker").classList.add("hidden");
  $("#feedback").classList.add("hidden");
  $("#bridge-status").classList.add("hidden");
  $("#tips-view").classList.add("hidden");
  $("#settings-view").classList.add("hidden");
  $("#dashboard-view").classList.add("hidden");

  const card = $("#card");
  card.classList.remove("hidden");
  clear(card);
  card.classList.remove("entering");
  void card.offsetWidth;
  card.classList.add("entering");

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
  const tips = currentTips()[key];
  const aside = $("#tips");
  if (!tips || !tips.length) {
    aside.classList.add("hidden");
    return;
  }
  const list = $("#tips-list");
  clear(list);

  // No tips during mock exam — emulate real test experience
  if (state.mockExam?.active) {
    aside.classList.add("hidden");
    return;
  }

  // 1. Tailored-for-this-question section at the TOP (if API key set)
  if (state.currentQ && aiAvailable()) {
    const tailoredBox = el("div", { class: "tailored-tips-box", id: "tailored-tips-box" });
    tailoredBox.appendChild(el("div", { class: "cat-label tailored-label" }, "For this question"));
    const cached = getCachedTailoredTips(state.currentQ.id);
    if (cached) {
      renderTailoredTipsInto(tailoredBox, cached);
    } else {
      tailoredBox.appendChild(el("div", { class: "tailored-status" },
        el("span", { class: "spinner spinner-sm" }),
        document.createTextNode(" Generating tips for this question..."),
      ));
      requestTailoredTips(state.currentQ, tailoredBox);
    }
    list.appendChild(tailoredBox);
  }

  // 2. Quick reminders — top 3 most useful tips, compactly. Eye-catching.
  // Skip if AI tailored tips already cover it (richer signal). Show 'See all'
  // link to drill into the full Tips browser for the complete list.
  const isGrouped = typeof tips[0] === "object" && tips[0] !== null;
  const quickTips = pickQuickTips(tips, isGrouped, 3);
  if (quickTips.length) {
    const quickBox = el("div", { class: "quick-tips-box" });
    quickBox.appendChild(el("div", { class: "quick-tips-header" },
      el("span", null, "Quick reminders"),
      el("a", {
        href: "#",
        class: "quick-tips-link",
        onclick: (e) => { e.preventDefault(); $("#tips-nav").click(); },
      }, "See all →"),
    ));
    const ul = el("ul", { class: "quick-tips-list" });
    for (const t of quickTips) ul.appendChild(el("li", null, t));
    quickBox.appendChild(ul);
    list.appendChild(quickBox);
  }
  aside.classList.remove("hidden");
}

// Pick the most actionable 1-N tips from a tips array (grouped or flat).
// Prefer 'Tricks' then 'Strategy' categories — those are the ones with the
// best "do this right now" advice. Skip 'Templates', 'Time', 'Scoring' which
// are reference material better served by the full Tips browser.
function pickQuickTips(tips, isGrouped, n) {
  if (!isGrouped) return tips.slice(0, n);
  const preferred = ["Tricks", "Strategy", "Traps"];
  const picks = [];
  for (const cat of preferred) {
    for (const t of tips) {
      if (t.cat === cat && !picks.includes(t.tip)) {
        picks.push(t.tip);
        if (picks.length >= n) return picks;
      }
    }
  }
  // Top up with anything remaining
  for (const t of tips) {
    if (t.tip && !picks.includes(t.tip)) {
      picks.push(t.tip);
      if (picks.length >= n) break;
    }
  }
  return picks;
}

// ---------- tailored tips (per-question LLM) ----------
const TAILORED_TIPS_CACHE = "pteracai_tailored_tips_cache_v1";
const TAILORED_TIPS_MAX = 50;

function getCachedTailoredTips(qid) {
  try {
    const all = JSON.parse(sessionStorage.getItem(TAILORED_TIPS_CACHE) || "{}");
    return all[qid] || null;
  } catch {
    return null;
  }
}

function cacheTailoredTips(qid, tipsArr) {
  try {
    let all = JSON.parse(sessionStorage.getItem(TAILORED_TIPS_CACHE) || "{}");
    all[qid] = tipsArr;
    // simple FIFO eviction
    const keys = Object.keys(all);
    if (keys.length > TAILORED_TIPS_MAX) {
      for (const k of keys.slice(0, keys.length - TAILORED_TIPS_MAX)) delete all[k];
    }
    sessionStorage.setItem(TAILORED_TIPS_CACHE, JSON.stringify(all));
  } catch {
    /* ignore quota */
  }
}

function requestTailoredTips(q, container) {
  postRequest({ kind: "tips", question: q }, (resp) => {
    if (resp.tailored_tips?.tips) {
      cacheTailoredTips(q.id, resp.tailored_tips.tips);
      renderTailoredTipsInto(container, resp.tailored_tips.tips);
    } else if (resp.error) {
      container.querySelector(".tailored-status")?.replaceWith(
        el("div", { class: "tailored-error" }, "Couldn't generate tailored tips.")
      );
    }
  }, { silent: true });
}

function renderTailoredTipsInto(container, tipsArr) {
  container.querySelector(".tailored-status")?.remove();
  const ul = el("ul", { class: "tailored-list" });
  for (const t of tipsArr) ul.appendChild(el("li", null, t));
  container.appendChild(ul);
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
  reading_mcq_single: { title: "Reading — Multiple Choice", subtitle: "Strategy for skimming, eliminating distractors, and avoiding paraphrase traps." },
  reading_reorder: { title: "Reading — Re-order Paragraphs", subtitle: "How to find the topic sentence and sequence using connectors, pronouns, and time markers." },
  reading_fib: { title: "Reading — Fill in the Blanks", subtitle: "Collocations, grammar matching, and high-leverage scoring across Reading + Writing." },
  reading_tfng: { title: "Reading — True / False / Not Given", subtitle: "The classic IELTS task. Mastering the False vs Not Given distinction is worth 2-3 band points." },
  reading_matching_headings: { title: "Reading — Matching Headings", subtitle: "Pick the best heading for each paragraph. The slowest reading task — do it last." },
  listening_wfd: { title: "Listening — Dictation & Sentence Completion", subtitle: "Type what you hear. The highest-leverage task in any English test — dual-scores Listening + Writing." },
  listening_sc: { title: "Listening — Sentence Completion", subtitle: "IELTS-style fill-in-blanks during a played audio. Preparation in the 30-second prep window is decisive." },
  listening_general: { title: "Listening — Other Tasks", subtitle: "Strategy for Summarize Spoken Text, Highlight Correct Summary, Fill in Blanks, and more." },
  listening_lst_mcq: { title: "Listening — Multiple Choice", subtitle: "Pre-audio reading of options is the most important habit you can build." },
  listening_lst_summary: { title: "Listening — Summarize Spoken Text", subtitle: "Dual-scores Listening + Writing. Template-based approach beats free composition." },
  listening_lst_sc: { title: "Listening — Sentence Completion", subtitle: "Read the printed sentence first to know what TYPE of word each blank needs." },
  writing_swt: { title: "Writing — Summarize Written Text", subtitle: "One-sentence summaries: templates, grammar structures, and PTE rubric breakdown." },
  writing_task1: { title: "Writing — Task 1 (Chart Description)", subtitle: "Describe a chart, graph, map, or process in 150+ words. The overview paragraph is critical." },
  writing_essay: { title: "Writing — Essay", subtitle: "5-paragraph templates, question-type identification, and connector rotation." },
  speaking_general: { title: "Speaking — Setup & Caveats", subtitle: "How speech recognition works here vs the real exam: what's graded, what isn't, and why." },
  speaking_read_aloud: { title: "Speaking — Read Aloud (PTE)", subtitle: "Read provided text aloud. Dual-scores Reading + Speaking — high leverage." },
  speaking_repeat_sentence: { title: "Speaking — Repeat Sentence (PTE)", subtitle: "Hear a sentence, repeat exactly. Dual-scores Listening + Speaking." },
  speaking_describe_image: { title: "Speaking — Describe Image (PTE)", subtitle: "25 seconds to describe a chart, map, or process. Templates beat improvisation." },
  speaking_retell_lecture: { title: "Speaking — Re-tell Lecture (PTE)", subtitle: "Hear/read a mini-lecture, re-tell in 40 seconds. Dual-scores Listening + Speaking." },
  speaking_answer_short: { title: "Speaking — Answer Short Question (PTE)", subtitle: "One-word answer, no elaboration. Speed > deliberation." },
  speaking_ielts_part1: { title: "Speaking — IELTS Part 1 (Familiar Topics)", subtitle: "2-3 sentence answers about your life, hobbies, and routine." },
  speaking_ielts_part2: { title: "Speaking — IELTS Part 2 (Cue Card)", subtitle: "1 min prep, 1-2 min monologue. Cover all bullets, don't trail off early." },
  speaking_ielts_part3: { title: "Speaking — IELTS Part 3 (Discussion)", subtitle: "Abstract questions. Position + example + nuance + hedged language." },
};

const TIPS_ORDER = [
  "exam",
  "reading_mcq_single",
  "reading_reorder",
  "reading_fib",
  "reading_tfng",
  "reading_matching_headings",
  "listening_wfd",
  "listening_sc",
  "listening_lst_mcq",
  "listening_lst_summary",
  "listening_lst_sc",
  "listening_general",
  "writing_swt",
  "writing_task1",
  "writing_essay",
  "speaking_general",
  "speaking_read_aloud",
  "speaking_repeat_sentence",
  "speaking_describe_image",
  "speaking_retell_lecture",
  "speaking_answer_short",
  "speaking_ielts_part1",
  "speaking_ielts_part2",
  "speaking_ielts_part3",
];

function renderTipsView() {
  $("#picker").classList.add("hidden");
  $("#card").classList.add("hidden");
  $("#feedback").classList.add("hidden");
  $("#bridge-status").classList.add("hidden");
  $("#tips").classList.add("hidden");
  $("#settings-view").classList.add("hidden");
  $("#dashboard-view").classList.add("hidden");
  state.currentFollowupOf = null;

  const view = $("#tips-view");
  view.classList.remove("hidden");
  clear(view);

  const testLabel = TEST_LABELS[state.test]?.short || "PTE";
  view.appendChild(el("h2", null, `${testLabel} Tips & Strategy`));
  view.appendChild(el(
    "div",
    { class: "subtitle" },
    `High-leverage, ${testLabel}-specific guidance for each phase of the exam. Click a section below to jump.`
  ));

  // table of contents
  const toc = el("div", { class: "tips-toc" });
  for (const key of TIPS_ORDER) {
    if (!currentTips()[key]) continue;
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
    const tips = currentTips()[key];
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
    let submitted = false;
    q.options.forEach((opt, idx) => {
      const o = el("div", { class: "option" }, opt);
      o.addEventListener("click", () => {
        if (submitted) return;
        opts.querySelectorAll(".option").forEach((x) => x.classList.remove("selected"));
        o.classList.add("selected");
        selected = idx;
      });
      opts.appendChild(o);
    });
    card.appendChild(opts);
    // Keyboard hint + handler
    const limit = Math.min(q.options.length, 9);
    card.appendChild(el(
      "div",
      { class: "kbd-hint" },
      "Press ",
      el("kbd", null, `1–${limit}`),
      " to select, ",
      el("kbd", null, "Enter"),
      " to submit"
    ));
    state.keyHandler = (e) => {
      if (submitted) return;
      if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.tagName === "SELECT") return;
      const n = parseInt(e.key, 10);
      if (!isNaN(n) && n >= 1 && n <= limit) {
        opts.querySelectorAll(".option").forEach((x) => x.classList.remove("selected"));
        opts.querySelectorAll(".option")[n - 1].classList.add("selected");
        selected = n - 1;
      } else if (e.key === "Enter" && selected >= 0) {
        submit();
      }
    };
    function submit() {
      if (submitted) return;
      submitted = true;
      const correct = checkAnswer(q, selected);
      recordAttempt(q, selected, correct);
      // Inline marking on the options themselves
      opts.querySelectorAll(".option").forEach((o, idx) => {
        o.classList.remove("selected");
        if (idx === q.answer) o.classList.add("correct");
        if (idx === selected && selected !== q.answer) o.classList.add("wrong");
      });
      showInlineFeedback(card, q, selected, correct);
    }
    card.appendChild(actionsBar(() => {
      if (selected < 0) return alert("Pick one option first.");
      submit();
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
    let submitted = false;
    card.appendChild(actionsBar(() => {
      if (submitted) return;
      submitted = true;
      const userOrder = order.slice();
      const correct = checkAnswer(q, userOrder);
      recordAttempt(q, userOrder, correct);
      // Show correct order under each paragraph row
      const rows = zone.querySelectorAll(".reorder-item");
      // user's display has paragraphs in `order` mapping; check each display position
      userOrder.forEach((displayIdx, correctPos) => {
        // The user's row at displayIdx claims correctPos
        const row = rows[displayIdx];
        if (!row) return;
        if (displayIdx === q.answer[correctPos]) row.classList.add("correct");
        else row.classList.add("wrong");
      });
      // Disable reorder buttons
      zone.querySelectorAll("button").forEach((b) => (b.disabled = true));
      showInlineFeedback(card, q, userOrder, correct);
    }));
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
    let submitted = false;
    card.appendChild(actionsBar(() => {
      if (submitted) return;
      if (selected.some((v) => v < 0)) return alert("Fill every blank first.");
      submitted = true;
      const correct = checkAnswer(q, selected);
      recordAttempt(q, selected, correct);
      // Annotate each dropdown with correct/wrong styling and show the right answer next to it
      wrap.querySelectorAll("select").forEach((sel, i) => {
        sel.disabled = true;
        const isRight = selected[i] === q.answer[i];
        sel.classList.add(isRight ? "fib-correct" : "fib-wrong");
        if (!isRight) {
          // Show correct answer inline
          const correctText = q.options[i][q.answer[i]];
          const marker = el("span", { class: "fib-correction" }, ` → ${correctText}`);
          sel.insertAdjacentElement("afterend", marker);
        }
      });
      showInlineFeedback(card, q, selected, correct);
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
    let submitted = false;
    card.appendChild(actionsBar(() => {
      if (submitted) return;
      submitted = true;
      const userAnswer = input.value.trim();
      const correct = checkAnswer(q, userAnswer);
      recordAttempt(q, userAnswer, correct);
      input.disabled = true;
      input.classList.add(correct ? "fib-correct" : "fib-wrong");
      if (!correct) {
        // Show the correct sentence directly below the textarea
        const corr = el("div", { class: "wfd-correction" },
          el("div", { class: "feedback-label" }, "Correct sentence"),
          el("div", { class: "passage" }, q.answer),
        );
        input.insertAdjacentElement("afterend", corr);
      }
      showInlineFeedback(card, q, userAnswer, correct);
    }));

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
    // IELTS essays want 250+, PTE wants 200-300; accept either as ok at 200+
    input.addEventListener("input", () => {
      const n = countWords(input.value);
      count.textContent = `${n} words`;
      count.className = "word-count " + (n >= 200 && n <= 320 ? "ok" : "bad");
    });
    card.appendChild(input);
    card.appendChild(count);
    card.appendChild(actionsBar(() => {
      if (countWords(input.value) < 50) return alert("Write at least a few paragraphs first.");
      submitForLLMGrading(q, input.value.trim());
    }));
  },

  // IELTS True / False / Not Given
  tfng(card, q) {
    card.appendChild(el("div", { class: "passage" }, q.passage));
    card.appendChild(el("div", { class: "qprompt" }, "Statement: ", el("em", null, q.statement)));
    card.appendChild(el("div", { class: "tfng-hint" }, "Is this statement TRUE according to the passage, FALSE according to the passage, or NOT GIVEN (not addressed)?"));
    let selected = null;
    let submitted = false;
    const opts = el("div", { class: "options tfng-options" });
    const entries = [
      { value: "true", label: "True", note: "passage confirms it" },
      { value: "false", label: "False", note: "passage contradicts it" },
      { value: "not given", label: "Not Given", note: "passage doesn't address it" },
    ];
    entries.forEach((entry) => {
      const o = el("div", { class: "option tfng-option" },
        el("div", { class: "tfng-label" }, entry.label),
        el("div", { class: "tfng-note" }, entry.note),
      );
      o.addEventListener("click", () => {
        if (submitted) return;
        opts.querySelectorAll(".option").forEach((x) => x.classList.remove("selected"));
        o.classList.add("selected");
        selected = entry.value;
      });
      opts.appendChild(o);
    });
    card.appendChild(opts);
    function submit() {
      if (submitted || selected == null) return;
      submitted = true;
      const correct = checkAnswer(q, selected);
      recordAttempt(q, selected, correct);
      // Mark options
      const nodes = opts.querySelectorAll(".option");
      entries.forEach((entry, i) => {
        nodes[i].classList.remove("selected");
        const isCorrect = entry.value.toLowerCase() === String(q.answer).toLowerCase();
        const isUserPick = entry.value === selected;
        if (isCorrect) nodes[i].classList.add("correct");
        if (isUserPick && !isCorrect) nodes[i].classList.add("wrong");
      });
      showInlineFeedback(card, q, selected, correct);
    }
    card.appendChild(actionsBar(() => {
      if (selected == null) return alert("Pick True, False, or Not Given.");
      submit();
    }));
  },

  // IELTS Matching Headings — for each paragraph, pick one heading from a shared bank
  matching_headings(card, q) {
    if (q.instructions) {
      card.appendChild(el("div", { class: "tfng-hint" }, q.instructions));
    }
    const selected = new Array(q.paragraphs.length).fill(-1);
    const wrap = el("div", { class: "mh-wrap" });
    q.paragraphs.forEach((para, pi) => {
      const row = el("div", { class: "mh-row" });
      row.appendChild(el("div", { class: "mh-para-num" }, `Paragraph ${pi + 1}`));
      row.appendChild(el("div", { class: "mh-para-text" }, para));
      const sel = el("select", {
        class: "mh-select",
        onchange: (e) => { selected[pi] = parseInt(e.target.value, 10); },
      });
      sel.appendChild(el("option", { value: "-1" }, "— choose a heading —"));
      q.headings.forEach((h, hi) => {
        sel.appendChild(el("option", { value: String(hi) }, `${String.fromCharCode(65 + hi)}. ${h}`));
      });
      row.appendChild(sel);
      wrap.appendChild(row);
    });
    card.appendChild(wrap);
    let submitted = false;
    card.appendChild(actionsBar(() => {
      if (submitted) return;
      if (selected.some((v) => v < 0)) return alert("Pick a heading for every paragraph.");
      submitted = true;
      const correct = checkAnswer(q, selected);
      recordAttempt(q, selected, correct);
      // Annotate each row with its result
      wrap.querySelectorAll(".mh-row").forEach((row, i) => {
        const sel = row.querySelector(".mh-select");
        sel.disabled = true;
        const isRight = selected[i] === q.answer[i];
        row.classList.add(isRight ? "mh-correct" : "mh-wrong");
        if (!isRight) {
          const correctHeading = q.headings[q.answer[i]];
          row.appendChild(el("div", { class: "mh-correction" },
            `Correct: ${String.fromCharCode(65 + q.answer[i])}. ${correctHeading}`));
        }
      });
      showInlineFeedback(card, q, selected, correct);
    }));
  },

  // ------------------- Listening expansions -------------------

  lst_mcq(card, q) {
    card.appendChild(el("div", { class: "qprompt" }, "Listen, then answer the question:"));
    const controls = el("div", { class: "wfd-controls" });
    controls.appendChild(el("button", { onclick: () => speak(q.audio_text) }, "▶  Play"));
    controls.appendChild(el("button", { onclick: () => speak(q.audio_text, 0.85) }, "▶  Play slow"));
    card.appendChild(controls);
    setTimeout(() => speak(q.audio_text), 300);

    card.appendChild(el("div", { class: "qprompt", style: "margin-top: 18px;" }, q.question));
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
    let submitted = false;
    card.appendChild(actionsBar(() => {
      if (submitted) return;
      if (selected < 0) return alert("Pick one option first.");
      submitted = true;
      // Use mcq_single checker logic by aliasing
      const aliased = { ...q, type: "mcq_single" };
      const correct = checkAnswer(aliased, selected);
      recordAttempt(q, selected, correct);
      opts.querySelectorAll(".option").forEach((o, idx) => {
        o.classList.remove("selected");
        if (idx === q.answer) o.classList.add("correct");
        if (idx === selected && selected !== q.answer) o.classList.add("wrong");
      });
      showInlineFeedback(card, q, selected, correct);
    }));
  },

  lst_summary(card, q) {
    card.appendChild(el("div", { class: "qprompt" }, "Listen, then summarize in 50-70 words:"));
    const controls = el("div", { class: "wfd-controls" });
    controls.appendChild(el("button", { onclick: () => speak(q.audio_text) }, "▶  Play lecture"));
    controls.appendChild(el("button", { onclick: () => speak(q.audio_text, 0.85) }, "▶  Play slow"));
    card.appendChild(controls);
    setTimeout(() => speak(q.audio_text), 300);

    const input = el("textarea", { class: "wfd-input", placeholder: "Write your summary (50-70 words)..." });
    const count = el("div", { class: "word-count" }, "0 words");
    input.addEventListener("input", () => {
      const n = countWords(input.value);
      count.textContent = `${n} words`;
      count.className = "word-count " + (n >= 50 && n <= 70 ? "ok" : "bad");
    });
    card.appendChild(input);
    card.appendChild(count);
    card.appendChild(actionsBar(() => {
      if (!input.value.trim()) return alert("Write your summary first.");
      submitForLLMGrading(q, input.value.trim());
    }));
  },

  lst_sc(card, q) {
    card.appendChild(el("div", { class: "qprompt" }, "Listen, then fill in the blanks in the sentence below:"));
    const controls = el("div", { class: "wfd-controls" });
    controls.appendChild(el("button", { onclick: () => speak(q.audio_text) }, "▶  Play"));
    controls.appendChild(el("button", { onclick: () => speak(q.audio_text, 0.85) }, "▶  Play slow"));
    card.appendChild(controls);
    setTimeout(() => speak(q.audio_text), 300);

    const wrap = el("div", { class: "fib-text", style: "margin-top: 16px;" });
    const inputs = [];
    q.text_parts.forEach((part, i) => {
      wrap.appendChild(document.createTextNode(part));
      if (i < q.answer.length) {
        const input = el("input", {
          type: "text",
          class: "lst-sc-input",
          autocomplete: "off",
          spellcheck: "true",
        });
        wrap.appendChild(input);
        inputs.push(input);
      }
    });
    card.appendChild(wrap);
    let submitted = false;
    card.appendChild(actionsBar(() => {
      if (submitted) return;
      const userAns = inputs.map((i) => i.value.trim());
      if (userAns.some((v) => !v)) return alert("Fill in every blank.");
      submitted = true;
      const norm = (s) => s.toLowerCase().replace(/[.,!?;:]/g, "").trim();
      const blankResults = userAns.map((v, idx) => norm(v) === norm(q.answer[idx]));
      const correct = blankResults.every(Boolean);
      recordAttempt(q, userAns, correct);
      // Annotate each input with correct/wrong + show right answer if wrong
      inputs.forEach((input, i) => {
        input.disabled = true;
        input.classList.add(blankResults[i] ? "fib-correct" : "fib-wrong");
        if (!blankResults[i]) {
          input.insertAdjacentElement("afterend",
            el("span", { class: "fib-correction" }, ` → ${q.answer[i]}`));
        }
      });
      showInlineFeedback(card, q, userAns, correct);
    }));
  },

  // ------------------- Speaking renderers -------------------

  read_aloud(card, q) {
    card.appendChild(el("div", { class: "qprompt" }, "Read the passage aloud:"));
    card.appendChild(el("div", { class: "passage" }, q.passage));
    const ui = buildSpeakingUI({
      card,
      hintText: "Click 'Start recording' when you're ready. Read at a natural pace, with intonation matching the punctuation.",
    });
    card.appendChild(ui.wrap);
    card.appendChild(actionsBar(() => {
      const t = ui.getTranscript();
      if (!t) return alert("Record yourself reading first.");
      submitForLLMGrading(q, t);
    }));
  },

  repeat_sentence(card, q) {
    card.appendChild(el("div", { class: "qprompt" }, "Listen, then repeat the sentence exactly:"));
    const ui = buildSpeakingUI({
      card,
      hintText: "The sentence plays automatically. Click 'Play sentence' to hear it again. Then click 'Start recording' and repeat.",
      allowAudioReplay: true,
      audioText: q.audio_text,
    });
    card.appendChild(ui.wrap);
    card.appendChild(actionsBar(() => {
      const t = ui.getTranscript();
      if (!t) return alert("Record yourself repeating first.");
      submitForLLMGrading(q, t);
    }));
  },

  describe_image(card, q) {
    card.appendChild(el("div", { class: "qprompt" }, q.prompt));
    const ui = buildSpeakingUI({
      card,
      hintText: "Speak for ~25 seconds. Use the template: intro, main feature, specific detail, overall conclusion.",
    });
    card.appendChild(ui.wrap);
    card.appendChild(actionsBar(() => {
      const t = ui.getTranscript();
      if (!t) return alert("Record yourself describing first.");
      submitForLLMGrading(q, t);
    }));
  },

  retell_lecture(card, q) {
    card.appendChild(el("div", { class: "qprompt" }, "Listen (or read), then re-tell the lecture in your own words:"));
    card.appendChild(el("div", { class: "passage" }, q.passage));
    const ui = buildSpeakingUI({
      card,
      hintText: "Click 'Start recording' when ready. Use template: 'The lecturer discussed... He/She explained... Furthermore... To conclude...'",
      allowAudioReplay: true,
      audioText: q.passage,
    });
    card.appendChild(ui.wrap);
    card.appendChild(actionsBar(() => {
      const t = ui.getTranscript();
      if (!t) return alert("Record yourself re-telling first.");
      submitForLLMGrading(q, t);
    }));
  },

  answer_short(card, q) {
    card.appendChild(el("div", { class: "qprompt" }, q.question));
    const ui = buildSpeakingUI({
      card,
      hintText: "Answer in one word or a short phrase. Respond immediately — hesitation costs.",
    });
    card.appendChild(ui.wrap);
    card.appendChild(actionsBar(() => {
      const t = ui.getTranscript();
      if (!t) return alert("Record yourself answering first.");
      submitForLLMGrading(q, t);
    }));
  },

  ielts_part1(card, q) {
    card.appendChild(el("div", { class: "qprompt" }, q.question));
    const ui = buildSpeakingUI({
      card,
      hintText: "2-3 sentence answer with a personal example. Match the question's tense.",
    });
    card.appendChild(ui.wrap);
    card.appendChild(actionsBar(() => {
      const t = ui.getTranscript();
      if (!t) return alert("Record yourself answering first.");
      submitForLLMGrading(q, t);
    }));
  },

  ielts_part2(card, q) {
    card.appendChild(el("div", { class: "qprompt", style: "white-space: pre-wrap;" }, q.prompt));
    const ui = buildSpeakingUI({
      card,
      hintText: "Take a moment to plan (4 keywords, one per bullet). Then record a 1-2 minute monologue covering all bullets.",
    });
    card.appendChild(ui.wrap);
    card.appendChild(actionsBar(() => {
      const t = ui.getTranscript();
      if (!t) return alert("Record yourself speaking first.");
      submitForLLMGrading(q, t);
    }));
  },

  ielts_part3(card, q) {
    card.appendChild(el("div", { class: "qprompt" }, q.question));
    const ui = buildSpeakingUI({
      card,
      hintText: "3-4 sentences. Position + example + nuance. Use 'arguably' / 'it seems' for hedging.",
    });
    card.appendChild(ui.wrap);
    card.appendChild(actionsBar(() => {
      const t = ui.getTranscript();
      if (!t) return alert("Record yourself answering first.");
      submitForLLMGrading(q, t);
    }));
  },

  // IELTS Writing Task 1 — same UX as essay but lower word floor
  task1(card, q) {
    card.appendChild(el("div", { class: "qprompt" }, q.prompt));
    const input = el("textarea", { class: "essay-input", placeholder: "Write your description here (150+ words)..." });
    const count = el("div", { class: "word-count" }, "0 words");
    input.addEventListener("input", () => {
      const n = countWords(input.value);
      count.textContent = `${n} words`;
      count.className = "word-count " + (n >= 150 && n <= 220 ? "ok" : "bad");
    });
    card.appendChild(input);
    card.appendChild(count);
    card.appendChild(actionsBar(() => {
      if (countWords(input.value) < 50) return alert("Write at least 50 words first.");
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

// ---------- Web Speech recognition wrapper ----------
function createSpeechRecognizer() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return null;
  const r = new SR();
  r.continuous = true;
  r.interimResults = true;
  r.lang = "en-US";
  return r;
}

function buildSpeakingUI({ card, onTranscript, hintText, allowAudioReplay, audioText }) {
  const wrap = el("div", { class: "speak-wrap" });

  if (hintText) {
    wrap.appendChild(el("div", { class: "tfng-hint" }, hintText));
  }

  if (allowAudioReplay && audioText) {
    const audioBtn = el("button", {
      class: "ghost",
      style: "margin-bottom: 14px;",
      onclick: () => speak(audioText),
    }, "▶  Play sentence");
    wrap.appendChild(audioBtn);
    setTimeout(() => speak(audioText), 300);
  }

  const status = el("div", { class: "speak-status" }, "Ready when you are.");
  wrap.appendChild(status);

  const transcript = el("div", { class: "speak-transcript", "aria-live": "polite" });
  wrap.appendChild(transcript);

  let recognizer = createSpeechRecognizer();
  let recording = false;
  let finalText = "";

  if (!recognizer) {
    status.textContent = "Speech recognition isn't supported in this browser. Try Chrome on desktop. You can still type your response below.";
    const fallback = el("textarea", { class: "wfd-input", placeholder: "Type your response..." });
    wrap.appendChild(fallback);
    return { wrap, getTranscript: () => fallback.value };
  }

  const micBtn = el("button", { class: "primary speak-mic" });

  function renderMic() {
    clear(micBtn);
    micBtn.appendChild(el("span", { class: "speak-mic-dot" }));
    micBtn.appendChild(document.createTextNode(recording ? "  Stop" : "  Start recording"));
    micBtn.classList.toggle("recording", recording);
  }
  renderMic();

  micBtn.addEventListener("click", () => {
    if (recording) {
      recognizer.stop();
    } else {
      finalText = "";
      transcript.textContent = "";
      try {
        recognizer.start();
      } catch (e) {
        status.textContent = "Couldn't start recording: " + e.message;
      }
    }
  });
  wrap.appendChild(micBtn);

  recognizer.onstart = () => {
    recording = true;
    status.textContent = "Listening… speak naturally.";
    renderMic();
  };
  recognizer.onerror = (e) => {
    status.textContent = "Recognition error: " + e.error + (e.error === "not-allowed" ? " (microphone permission denied)" : "");
    recording = false;
    renderMic();
  };
  recognizer.onend = () => {
    recording = false;
    status.textContent = finalText ? "Recording stopped. Submit when ready." : "Recording stopped — nothing captured.";
    renderMic();
    onTranscript?.(finalText);
  };
  recognizer.onresult = (e) => {
    let interim = "";
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const r = e.results[i];
      if (r.isFinal) finalText += r[0].transcript + " ";
      else interim += r[0].transcript;
    }
    transcript.textContent = (finalText + interim).trim();
  };

  return { wrap, getTranscript: () => finalText.trim() };
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
  // Inline mode: feedback rendered into the question card itself (modern UX).
  // Each renderer that supports inline mode marks its widgets and calls
  // showInlineFeedback(). Legacy fallback to showFeedback for types that
  // haven't been migrated yet.
  showFeedback(q, userAnswer, correct);
}

// Renders inline feedback into the question card (below the options/widgets).
// Replaces the actions bar at the bottom of the card with feedback + new actions.
function showInlineFeedback(card, q, userAnswer, correct) {
  // Remove the original actions bar
  card.querySelectorAll('.actions').forEach((a) => a.remove());

  const inMock = state.mockExam?.active;
  const fb = el('div', { class: 'inline-feedback' });
  fb.appendChild(el(
    'div',
    { class: 'inline-verdict ' + (correct ? 'correct' : 'wrong') },
    correct ? '✓ Correct' : '✗ Not quite'
  ));

  // In mock mode, suppress detailed teaching feedback — emulate the real test
  // experience where you don't get explanations between questions. User sees
  // just the verdict, then advances. Full breakdown comes at the end.
  if (inMock) {
    const actions = el('div', { class: 'actions' });
    const isLast = state.mockExam.index >= state.mockExam.queue.length - 1;
    actions.appendChild(el('button', {
      class: 'primary',
      onclick: () => advanceMock(),
    }, isLast ? 'Finish mock' : 'Next question →'));
    actions.appendChild(el('button', { class: 'ghost', onclick: () => finishMockExam() }, 'End mock early'));
    fb.appendChild(actions);
    card.appendChild(fb);
    return;
  }

  // Bank explanation (always shown — it's the "why" reference)
  if (q.explanation) {
    fb.appendChild(el('div', { class: 'feedback-label' }, 'Why'));
    fb.appendChild(el('div', { class: 'feedback-explanation' }, q.explanation));
  }

  // Trap warning (wrong only)
  if (!correct && q.trap) {
    fb.appendChild(el(
      'div',
      { class: 'feedback-trap' },
      el('div', { class: 'feedback-label' }, 'Watch out for'),
      q.trap
    ));
  }

  // AI analysis (wrong + AI available + not LLM-graded)
  const llmGraded = new Set(['swt', 'essay', 'task1', 'lst_summary',
    'read_aloud', 'repeat_sentence', 'describe_image', 'retell_lecture',
    'answer_short', 'ielts_part1', 'ielts_part2', 'ielts_part3']);
  if (!correct && aiAvailable() && !llmGraded.has(q.type)) {
    const analyzeBox = el('div', { class: 'feedback-analyze' },
      el('div', { class: 'feedback-label' }, 'AI analysis of your answer'),
      el('div', { class: 'analyze-status' },
        el('span', { class: 'spinner spinner-sm' }),
        document.createTextNode(' Analyzing...')
      ),
    );
    fb.appendChild(analyzeBox);
    requestAnalysis(q, userAnswer, analyzeBox);
  }

  // Action buttons
  const actions = el('div', { class: 'actions' });
  if (correct && state.currentFollowupOf) {
    state.currentFollowupOf = null;
    actions.appendChild(el('button', { class: 'primary', onclick: () => renderPicker() }, 'Mastery confirmed ✓ — next topic'));
  } else if (correct) {
    actions.appendChild(el('button', { class: 'primary', onclick: () => pickByType(q.type) }, 'Next question'));
    actions.appendChild(el('button', { class: 'ghost', onclick: () => renderPicker() }, 'Back to picker'));
  } else {
    actions.appendChild(el('button', { class: 'primary', onclick: () => requestFollowup(q) }, 'Try a similar one'));
    if (state.pendingCoaching && aiAvailable()) {
      actions.appendChild(el('button', {
        class: 'primary coach-btn',
        onclick: () => requestCoaching(q, state.pendingCoaching.streak),
      }, `Coach Mode (${state.pendingCoaching.streak} in a row)`));
    }
    actions.appendChild(el('button', { class: 'ghost', onclick: () => pickByType(q.type) }, 'Skip'));
    actions.appendChild(el('button', { class: 'ghost', onclick: () => renderPicker() }, 'Back to picker'));
  }
  fb.appendChild(actions);
  card.appendChild(fb);
  // Smooth scroll to feedback
  fb.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function checkAnswer(q, ans) {
  if (q.type === "mcq_single") return ans === q.answer;
  if (q.type === "reorder") return JSON.stringify(ans) === JSON.stringify(q.answer);
  if (q.type === "fib") return JSON.stringify(ans) === JSON.stringify(q.answer);
  if (q.type === "wfd") {
    const norm = (s) => s.toLowerCase().replace(/[.,!?;:]/g, "").replace(/\s+/g, " ").trim();
    return norm(ans) === norm(q.answer);
  }
  if (q.type === "tfng") {
    return String(ans).toLowerCase() === String(q.answer).toLowerCase();
  }
  if (q.type === "matching_headings") {
    return JSON.stringify(ans) === JSON.stringify(q.answer);
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
  bumpStreakChip();

  // Local + Drive-synced persistence — tag with the active test so the
  // dashboard can filter per-test stats accurately.
  const streakInfo = appendAttempt({
    ts: Date.now(),
    qid: q.id,
    test: state.test,
    section: q.section,
    type: q.type,
    topic: q.topic,
    correct,
    user_answer: userAnswer,
    is_followup_of: state.currentFollowupOf,
    mock: state.mockExam?.active || false,
  });

  // Local file-bridge logging (no-op on Vercel — endpoint returns nothing)
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
  }).catch(() => {});

  // Adaptive coaching trigger: 3+ consecutive wrong on same task type+topic
  if (!correct && streakInfo.wrong_in_a_row >= 3 && aiAvailable()) {
    state.pendingCoaching = { question: q, streak: streakInfo.wrong_in_a_row };
  }
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

  // If wrong + API key configured + this is an auto-graded type,
  // fire a tailored analysis of THEIR specific wrong answer.
  // SWT and essay already go through LLM grading, so no extra call needed for those.
  const llmGradedTypes = new Set(["swt", "essay", "task1", "lst_summary",
    "read_aloud", "repeat_sentence", "describe_image", "retell_lecture",
    "answer_short", "ielts_part1", "ielts_part2", "ielts_part3"]);
  if (!correct && aiAvailable() && !llmGradedTypes.has(q.type)) {
    const analyzeBox = el("div", { class: "feedback-analyze" },
      el("div", { class: "feedback-label" }, "AI analysis of your answer"),
      el("div", { class: "analyze-status" },
        el("span", { class: "spinner spinner-sm" }),
        document.createTextNode(" Analyzing your specific answer..."),
      ),
    );
    fb.appendChild(analyzeBox);
    requestAnalysis(q, userAnswer, analyzeBox);
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
    if (state.pendingCoaching && aiAvailable()) {
      actions.appendChild(el(
        "button",
        {
          class: "primary coach-btn",
          onclick: () => requestCoaching(q, state.pendingCoaching.streak),
        },
        `Coach Mode (${state.pendingCoaching.streak} in a row)`
      ));
    }
    actions.appendChild(el("button", { class: "ghost", onclick: () => pickByType(q.type) }, "Skip, new question"));
    actions.appendChild(el("button", { class: "ghost", onclick: () => renderPicker() }, "Back to picker"));
  }
  fb.appendChild(actions);
}

function requestAnalysis(q, userAnswer, container) {
  // Send a sanitized copy of the question + the user's specific wrong answer.
  // Include the correct answer in the question for context.
  const request = {
    kind: "analyze",
    question: q,
    user_answer: userAnswer,
  };
  postRequest(request, (resp) => {
    if (resp.analysis) renderAnalysis(container, resp.analysis);
    else if (resp.error) {
      container.querySelector(".analyze-status")?.replaceWith(
        el("div", { class: "analyze-error" }, "Analysis failed: " + resp.error)
      );
    }
  }, { silent: true });
}

function renderAnalysis(container, a) {
  const status = container.querySelector(".analyze-status");
  if (status) status.remove();
  if (a.diagnosis) {
    container.appendChild(el("div", { class: "analyze-line" },
      el("strong", null, "What happened: "),
      document.createTextNode(a.diagnosis),
    ));
  }
  if (a.comparison) {
    container.appendChild(el("div", { class: "analyze-line" },
      el("strong", null, "The correct answer: "),
      document.createTextNode(a.comparison),
    ));
  }
  if (a.fix) {
    container.appendChild(el("div", { class: "analyze-line analyze-fix" },
      el("strong", null, "Next time: "),
      document.createTextNode(a.fix),
    ));
  }
}

function requestCoaching(q, streak) {
  const p = loadProgress();
  const recent = p.attempts
    .filter((a) => a.section === q.section && a.type === q.type && a.topic === q.topic)
    .slice(-5);
  const recentWithQ = recent.map((a) => {
    const fullQ = currentQuestions().find((x) => x.id === a.qid) || { id: a.qid };
    return { question: fullQ, user_answer: a.user_answer, correct: a.correct };
  });
  postRequest(
    {
      kind: "coach",
      section: q.section,
      type: q.type,
      topic: q.topic,
      consecutive_wrong: streak,
      recent_attempts: recentWithQ,
    },
    (resp) => {
      if (resp.coaching) {
        showCoaching(q, resp.coaching);
        state.pendingCoaching = null;
      } else if (resp.error) {
        alert("Coaching failed: " + resp.error);
      }
    }
  );
}

function showCoaching(q, coaching) {
  const fb = $("#feedback");
  clear(fb);
  fb.classList.remove("hidden");
  fb.appendChild(el("div", { class: "feedback-verdict", style: "color: #8a6f1e;" }, "Coach Mode"));
  if (coaching.diagnosis) {
    fb.appendChild(el("div", { class: "feedback-label" }, "What's going wrong"));
    fb.appendChild(el("div", { class: "feedback-explanation" }, coaching.diagnosis));
  }
  if (Array.isArray(coaching.micro_tips) && coaching.micro_tips.length) {
    fb.appendChild(el("div", { class: "feedback-label" }, "Targeted fixes"));
    const ul = el("ul", null);
    coaching.micro_tips.forEach((t) => ul.appendChild(el("li", null, t)));
    fb.appendChild(ul);
  }
  if (coaching.drill_focus) {
    fb.appendChild(el("div", { class: "feedback-label" }, "Drill recommendation"));
    fb.appendChild(el("div", { class: "feedback-explanation" }, coaching.drill_focus));
  }
  const actions = el("div", { class: "actions" });
  actions.appendChild(el("button", { class: "primary", onclick: () => requestFollowup(q) }, "Try a fresh drill on this skill"));
  actions.appendChild(el("button", { class: "ghost", onclick: () => renderPicker() }, "Back to picker"));
  fb.appendChild(actions);
}

function answerDisplay(q) {
  const wrap = el("div", { class: "feedback-explanation" });
  wrap.appendChild(el("div", { class: "feedback-label" }, "Correct answer"));
  if (q.type === "tfng") {
    wrap.appendChild(el("div", null, String(q.answer).toUpperCase()));
  } else if (q.type === "mcq_single") {
    wrap.appendChild(el("div", null, q.options[q.answer]));
  } else if (q.type === "reorder") {
    const ol = el("ol", null);
    q.answer.forEach((idx) => ol.appendChild(el("li", null, q.paragraphs[idx])));
    wrap.appendChild(ol);
  } else if (q.type === "fib") {
    wrap.appendChild(el("div", null, q.answer.map((idx, i) => q.options[i][idx]).join("  /  ")));
  } else if (q.type === "wfd") {
    wrap.appendChild(el("div", { class: "passage" }, q.answer));
  } else if (q.type === "matching_headings") {
    const ol = el("ol", null);
    q.answer.forEach((headingIdx, paraIdx) => {
      ol.appendChild(el("li", null, `Paragraph ${paraIdx + 1} → ${String.fromCharCode(65 + headingIdx)}. ${q.headings[headingIdx]}`));
    });
    wrap.appendChild(ol);
  } else if (q.type === "lst_sc_display" || q.type === "lst_sc") {
    wrap.appendChild(el("div", null, q.answer.join("  /  ")));
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

async function postRequest(request, handler, opts = {}) {
  // opts.silent = true → skip the full-screen bridge spinner. Use for
  // background calls (tips, analysis) that have their own inline indicators.
  const silent = !!opts.silent;
  const settings = loadSettings();
  const headers = { "Content-Type": "application/json" };
  let usingFreeTier = false;

  if (settings) {
    // User has their own key configured.
    headers["x-provider"] = settings.provider;
    headers["x-api-key"] = settings.apiKey;
    if (settings.model) headers["x-model"] = settings.model;
  } else if (freeTierUsable()) {
    // Use the shared free tier — send no key headers, server falls back to OPENROUTER_FREE_KEY.
    usingFreeTier = true;
    incrementFreeTierUsage();
    updateFreeTierBadge();
  } else if (state.freeTierAvailable && freeTierRemaining() === 0) {
    // Free tier exists but visitor exhausted today's quota.
    const wantsKey = confirm(
      `You've used today's free AI quota (${FREE_TIER_QUOTA} requests).\n\n` +
      "Add your own API key for unlimited use? You can use Anthropic, OpenAI, or OpenRouter — most have free signup credits.\n\n" +
      "Click OK to open Settings."
    );
    if (wantsKey) $("#settings-nav").click();
    return;
  } else {
    // No free tier configured AND no user key. Local dev or owner hasn't set up free tier.
    const wantsConfig = confirm(
      "This action needs an AI provider key.\n\n" +
      "If you're running PteracAI locally with Claude Code in your terminal, you can ignore this.\n\n" +
      "Otherwise click OK to open Settings and add your key (Anthropic / OpenAI / OpenRouter — free signup available)."
    );
    if (wantsConfig) $("#settings-nav").click();
    return;
  }

  if (!silent) showBridgeStatus(true);
  let res;
  try {
    res = await fetch("/api/request", {
      method: "POST",
      headers,
      body: JSON.stringify(request),
    });
  } catch (e) {
    if (!silent) showBridgeStatus(false);
    if (!silent) alert("Network error: " + e.message);
    return;
  }

  if (!res.ok) {
    if (!silent) showBridgeStatus(false);
    let msg = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (body?.error) msg = body.error;
    } catch (_) {}
    if (silent) {
      // surface error via handler so caller can render it inline
      handler({ error: msg });
    } else {
      alert("Request failed: " + msg);
    }
    return;
  }

  const body = await res.json();

  // Vercel mode: response contains the full payload synchronously.
  if (body.question || body.grading || body.tailored_tips || body.analysis || body.coaching) {
    if (!silent) showBridgeStatus(false);
    handler(body);
    return;
  }

  // Local file-bridge mode: response acknowledges with an id; poll for the result.
  if (body.id) {
    state.inflightById.set(body.id, handler);
    return;
  }

  if (!silent) showBridgeStatus(false);
  if (silent) handler({ error: "Unexpected response shape" });
  else alert("Unexpected response from /api/request.");
}

function showBridgeStatus(visible) {
  $("#bridge-status").classList.toggle("hidden", !visible);
  const hint = $("#bridge-hint");
  if (!visible) {
    if (state.bridgeHintTimer) clearTimeout(state.bridgeHintTimer);
    hint.classList.add("hidden");
    return;
  }
  // Update label to reflect what's actually being used
  const txt = $("#bridge-text");
  if (txt) {
    const s = loadSettings();
    if (s) {
      const label = { anthropic: "Claude", openai: "GPT", openrouter: "OpenRouter" }[s.provider] || "AI";
      txt.textContent = `Generating with ${label}...`;
    } else if (state.freeTierAvailable) {
      txt.textContent = "Generating with free AI...";
    } else {
      txt.textContent = "Generating...";
    }
  }
  hint.classList.add("hidden");
  // Only show the "tell Claude Code in your terminal" hint on localhost.
  const isLocalhost = ["localhost", "127.0.0.1"].includes(location.hostname);
  if (!isLocalhost) return;
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
  $("#dashboard-view").classList.add("hidden");

  const view = $("#settings-view");
  view.classList.remove("hidden");
  clear(view);

  view.appendChild(el("h2", null, "Settings — Bring Your Own AI Key"));
  view.appendChild(el(
    "div",
    { class: "subtitle" },
    "PteracAI is free to use. You bring your own API key from the provider of your choice. Your key is stored only in this browser and is never logged on the server."
  ));

  // Free tier status banner (shown when free tier is available)
  if (state.freeTierAvailable) {
    const left = freeTierRemaining();
    const usingFree = !loadSettings();
    const banner = el("div", {
      class: "settings-status show " + (left === 0 ? "err" : (usingFree ? "ok" : "info")),
      style: "margin-bottom: 24px;",
    });
    if (usingFree && left > 0) {
      banner.appendChild(document.createTextNode(
        `You're using the shared free AI tier (${left}/${FREE_TIER_QUOTA} requests left today). Models cascade across free Llama/Gemma/Mistral. Add your own key below for unlimited use and higher-quality models.`
      ));
    } else if (usingFree && left === 0) {
      banner.appendChild(document.createTextNode(
        `You've used all ${FREE_TIER_QUOTA} free AI requests for today. Quota resets at midnight UTC. To keep going now, add your own key below — most providers offer free signup credits.`
      ));
    } else {
      banner.appendChild(document.createTextNode(
        `A shared free AI tier is available (${FREE_TIER_QUOTA} requests/day). It's currently disabled because you have your own key configured below. To use the free tier, clear your stored key.`
      ));
    }
    view.appendChild(banner);
  }

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

  // --- Score profile section ---
  view.appendChild(el("h2", { style: "margin-top: 36px;" }, "Test score profile"));
  view.appendChild(el(
    "div",
    { class: "subtitle" },
    "Upload your latest PTE or IELTS score report PDF — the AI extracts your scores and builds a targeted improvement plan that appears on your dashboard. You can also enter scores manually if you don't have the PDF."
  ));
  renderScoreProfileSection(view);

  // --- Google Drive sync section ---
  view.appendChild(el("h2", { style: "margin-top: 36px;" }, "Cross-device sync"));
  view.appendChild(el(
    "div",
    { class: "subtitle" },
    "Sign in with Google to sync your settings, attempt history, and spaced-repetition queue across devices. Data is stored in a hidden folder in YOUR Google Drive — the app owner never sees it."
  ));
  renderSyncSection(view);
}

function renderScoreProfileSection(view) {
  const wrap = el("div", null);
  const profile = loadScoreProfile();

  if (profile && profile.analysis) {
    // Show current profile
    const card = el("div", { class: "settings-status show ok" });
    card.appendChild(document.createTextNode(
      `Profile saved: ${profile.analysis.test?.toUpperCase()} · overall ${profile.analysis.overall_score} / ${profile.analysis.max_score} · weakest: ${profile.analysis.weakest_skill}. Improvement plan is shown on your dashboard.`
    ));
    wrap.appendChild(card);
    const actions = el("div", { class: "settings-actions" });
    actions.appendChild(el("button", {
      class: "ghost",
      onclick: () => {
        if (confirm("Clear your saved score profile?")) {
          clearScoreProfile();
          renderSettingsView();
        }
      },
    }, "Clear saved profile"));
    actions.appendChild(el("button", {
      class: "ghost",
      onclick: () => {
        // Show upload UI again to replace
        card.classList.add("hidden");
        actions.classList.add("hidden");
        renderScoreProfileInput(wrap);
      },
    }, "Replace with new report"));
    wrap.appendChild(actions);
  } else {
    renderScoreProfileInput(wrap);
  }
  view.appendChild(wrap);
}

function renderScoreProfileInput(wrap) {
  const inputBox = el("div", null);

  // File upload zone
  const upload = el("div", { class: "score-upload-zone" });
  upload.appendChild(el("div", { class: "score-upload-icon" }, "📄"));
  upload.appendChild(el("div", { class: "score-upload-text" }, "Drop your score report PDF here, or click to browse"));
  const fileInput = el("input", {
    type: "file",
    accept: "application/pdf",
    style: "display: none;",
  });
  upload.appendChild(fileInput);
  upload.addEventListener("click", () => fileInput.click());
  upload.addEventListener("dragover", (e) => {
    e.preventDefault();
    upload.classList.add("dragover");
  });
  upload.addEventListener("dragleave", () => upload.classList.remove("dragover"));
  upload.addEventListener("drop", (e) => {
    e.preventDefault();
    upload.classList.remove("dragover");
    const f = e.dataTransfer?.files?.[0];
    if (f) handlePdf(f);
  });
  fileInput.addEventListener("change", (e) => {
    const f = e.target.files?.[0];
    if (f) handlePdf(f);
  });
  inputBox.appendChild(upload);

  // Status / progress
  const status = el("div", { class: "settings-status", id: "score-status" });
  inputBox.appendChild(status);

  // Manual fallback
  const manualToggle = el("details", { class: "score-manual" });
  manualToggle.appendChild(el("summary", null, "Don't have the PDF? Enter scores manually →"));
  const form = el("div", { class: "score-manual-form" });
  const testSel = el("select", null,
    el("option", { value: "pte" }, "PTE Academic"),
    el("option", { value: "ielts" }, "IELTS Academic"),
  );
  testSel.value = state.test;
  form.appendChild(el("div", { class: "settings-row" },
    el("label", null, "Test"), testSel));
  const scoreInputs = {};
  function rebuildScoreInputs() {
    form.querySelectorAll(".manual-score-row").forEach((r) => r.remove());
    const isPte = testSel.value === "pte";
    const skills = isPte
      ? ["Reading", "Listening", "Writing", "Speaking", "Overall"]
      : ["Listening", "Reading", "Writing", "Speaking", "Overall"];
    skills.forEach((s) => {
      const input = el("input", {
        type: "number",
        step: isPte ? "1" : "0.5",
        min: isPte ? "10" : "1",
        max: isPte ? "90" : "9",
        placeholder: isPte ? "e.g. 65" : "e.g. 6.5",
      });
      scoreInputs[s] = input;
      const row = el("div", { class: "settings-row manual-score-row" },
        el("label", null, s), input);
      form.appendChild(row);
    });
  }
  rebuildScoreInputs();
  testSel.addEventListener("change", rebuildScoreInputs);
  const submitManual = el("button", { class: "primary", style: "margin-top: 12px;" }, "Build my plan from these scores");
  submitManual.addEventListener("click", () => {
    const test = testSel.value;
    const scores = {};
    for (const [name, input] of Object.entries(scoreInputs)) {
      const v = parseFloat(input.value);
      if (!isNaN(v)) scores[name] = v;
    }
    if (Object.keys(scores).length === 0) return alert("Enter at least one score.");
    analyzeScores({ test, manual_scores: scores });
  });
  form.appendChild(submitManual);
  manualToggle.appendChild(form);
  inputBox.appendChild(manualToggle);

  wrap.appendChild(inputBox);

  async function handlePdf(file) {
    status.className = "settings-status show info";
    status.textContent = "Reading PDF...";
    try {
      const text = await extractTextFromPDF(file);
      if (!text || text.length < 50) {
        status.className = "settings-status show err";
        status.textContent = "Couldn't read meaningful text from this PDF. Try the manual form below.";
        return;
      }
      status.textContent = `Extracted ${text.length} characters. Asking AI to parse and build your plan...`;
      analyzeScores({ test: state.test, report_text: text });
    } catch (e) {
      status.className = "settings-status show err";
      status.textContent = "PDF read failed: " + e.message;
    }
  }

  function analyzeScores(payload) {
    if (!aiAvailable()) {
      status.className = "settings-status show err";
      status.textContent = "Add an AI key in Settings (or use the free tier) before analyzing scores.";
      return;
    }
    status.className = "settings-status show info";
    status.textContent = "Analyzing your scores and building an improvement plan... (5-10 seconds)";
    postRequest({ kind: "score_analysis", ...payload }, (resp) => {
      if (resp.score_analysis) {
        const a = resp.score_analysis;
        if (a.error) {
          status.className = "settings-status show err";
          status.textContent = a.error;
          return;
        }
        saveScoreProfile({ source: payload.report_text ? "pdf" : "manual", analysis: a });
        status.className = "settings-status show ok";
        status.textContent = "Score profile saved. Open the Home tab to see your plan.";
        // Refresh settings view to show the saved-state card
        setTimeout(() => renderSettingsView(), 600);
      } else if (resp.error) {
        status.className = "settings-status show err";
        status.textContent = "Analysis failed: " + resp.error;
      }
    }, { silent: true });
  }
}

function renderSyncSection(view) {
  const wrap = el("div", null);

  if (!window.PteracaiSync || !PteracaiSync.configured()) {
    const note = el("div", { class: "settings-status show info" });
    note.appendChild(document.createTextNode(
      "Google sync is not configured on this deployment. To enable: the site owner creates a Google OAuth Client ID and sets window.PTERACAI_GOOGLE_CLIENT_ID. See "
    ));
    note.appendChild(el("a", { href: REPO_URL + "#google-sign-in-setup", target: "_blank", rel: "noopener" }, "README"));
    note.appendChild(document.createTextNode(" for the 3-minute walkthrough."));
    wrap.appendChild(note);
    view.appendChild(wrap);
    return;
  }

  const isIn = PteracaiSync.signedIn();
  const u = PteracaiSync.user();

  if (isIn && u) {
    const status = el("div", { class: "settings-status show ok" });
    status.appendChild(document.createTextNode(`Signed in as ${u.name || u.email}. Your progress is syncing to your Google Drive.`));
    wrap.appendChild(status);

    const actions = el("div", { class: "settings-actions" });
    const syncNowBtn = el("button", { class: "ghost" }, "Sync now");
    syncNowBtn.addEventListener("click", async () => {
      syncNowBtn.disabled = true;
      syncNowBtn.textContent = "Syncing...";
      try {
        await pullAndMerge();
        await PteracaiSync.push({
          schema_version: 1,
          settings: loadSettings(),
          settings_updated: Number(localStorage.getItem("pteracai_settings_updated") || 0),
          progress: loadProgress(),
        });
        syncNowBtn.textContent = "Synced ✓";
      } catch (e) {
        syncNowBtn.textContent = "Sync failed";
        console.warn(e);
      }
      setTimeout(() => {
        syncNowBtn.disabled = false;
        syncNowBtn.textContent = "Sync now";
      }, 1500);
    });
    const signOutBtn = el("button", { class: "ghost" }, "Sign out");
    signOutBtn.addEventListener("click", () => {
      PteracaiSync.signOut();
      renderSettingsView();
    });
    actions.appendChild(syncNowBtn);
    actions.appendChild(signOutBtn);
    wrap.appendChild(actions);
  } else {
    const signInBtn = el("button", { class: "primary" }, "Sign in with Google");
    signInBtn.addEventListener("click", async () => {
      try {
        await PteracaiSync.signIn();
      } catch (e) {
        alert("Google sign-in failed: " + e.message);
      }
    });
    wrap.appendChild(signInBtn);
  }

  // Privacy disclosure for sync
  const syncPrivacy = el("div", { class: "settings-privacy", style: "margin-top: 18px;" });
  syncPrivacy.appendChild(el("h4", null, "What gets synced"));
  const ul = el("ul", null);
  ul.appendChild(el("li", null, "Settings — provider, API key, model"));
  ul.appendChild(el("li", null, "Practice attempts — what you answered and whether it was correct"));
  ul.appendChild(el("li", null, "Spaced repetition queue — when missed questions resurface"));
  syncPrivacy.appendChild(ul);
  syncPrivacy.appendChild(el(
    "div",
    { style: "margin-top: 10px;" },
    "Note: Your API key is included in the synced data. Anyone with access to your Google account can read it via Drive. The app owner cannot see it — data lives in YOUR Drive's hidden app folder."
  ));
  wrap.appendChild(syncPrivacy);

  view.appendChild(wrap);

  function setStatus(kind, msg) {
    status.className = "settings-status show " + kind;
    status.textContent = msg;
  }
}

// ============================================================================
// PROGRESS DASHBOARD — the new home screen
// ============================================================================
function renderDashboardView() {
  $("#picker").classList.add("hidden");
  $("#card").classList.add("hidden");
  $("#feedback").classList.add("hidden");
  $("#bridge-status").classList.add("hidden");
  $("#tips").classList.add("hidden");
  $("#tips-view").classList.add("hidden");
  $("#settings-view").classList.add("hidden");

  const view = $("#dashboard-view");
  view.classList.remove("hidden");
  clear(view);

  const stats = computeStats();
  const p = loadProgress();

  // ---- Hero greeting ----
  const hero = el("div", { class: "dash-hero" });
  const u = window.PteracaiSync?.user?.();
  const greet = u?.name ? `Welcome back, ${u.name.split(" ")[0]}` : "Welcome back";
  hero.appendChild(el("h1", { class: "dash-greeting" }, greet));
  hero.appendChild(el("div", { class: "dash-subtext" },
    stats.totalAttempts === 0
      ? `Ready to start? Pick a section above to practice your first ${TEST_LABELS[state.test]?.short || "PTE"} question.`
      : `${stats.totalAttempts} questions practiced · ${stats.overallAccuracy}% overall accuracy`
  ));
  view.appendChild(hero);

  // ---- Today's progress card ----
  const todayCard = el("div", { class: "dash-card dash-today" });
  todayCard.appendChild(el("div", { class: "dash-card-label" }, "Today"));
  const todayInner = el("div", { class: "dash-today-grid" });
  todayInner.appendChild(makeStat(stats.todayAttempts, "questions", "dash-stat-primary"));
  todayInner.appendChild(makeStat(
    stats.todayAttempts > 0 ? `${Math.round(stats.todayAccuracy)}%` : "—",
    "accuracy"
  ));
  todayInner.appendChild(makeStat(stats.dailyStreak, stats.dailyStreak === 1 ? "day streak" : "days streak"));
  todayInner.appendChild(makeStat(stats.dueCount, "due for review"));
  todayCard.appendChild(todayInner);
  // Daily-goal progress bar (default: 10 questions/day)
  const goal = 10;
  const goalPct = Math.min(100, Math.round((stats.todayAttempts / goal) * 100));
  todayCard.appendChild(el("div", { class: "dash-goal-row" },
    el("div", { class: "dash-goal-label" }, `Daily goal: ${stats.todayAttempts}/${goal}`),
    el("div", { class: "dash-goal-bar" },
      el("div", { class: "dash-goal-fill", style: `width: ${goalPct}%` })
    ),
  ));
  view.appendChild(todayCard);

  // ---- Next actions row ----
  if (stats.totalAttempts > 0) {
    const actions = el("div", { class: "dash-actions-row" });
    if (stats.dueCount > 0) {
      actions.appendChild(el("button", {
        class: "primary dash-action-btn",
        onclick: () => practiceDue(),
      }, `Review ${stats.dueCount} due question${stats.dueCount === 1 ? "" : "s"}`));
    }
    if (stats.weakestType) {
      actions.appendChild(el("button", {
        class: "ghost dash-action-btn",
        onclick: () => {
          state.section = stats.weakestType.section;
          $$(".section-btn[data-section]").forEach((b) =>
            b.classList.toggle("active", b.dataset.section === stats.weakestType.section));
          $("#home-nav").classList.remove("active");
          pickByType(stats.weakestType.type);
        },
      }, `Drill your weakest: ${TYPE_NAMES[stats.weakestType.type]?.[0] || stats.weakestType.type} (${stats.weakestType.accuracy}%)`));
    }
    actions.appendChild(el("button", {
      class: "ghost dash-action-btn",
      onclick: () => {
        $$(".section-btn[data-section]").forEach((b) =>
          b.classList.toggle("active", b.dataset.section === "reading"));
        $("#home-nav").classList.remove("active");
        state.section = "reading";
        renderPicker();
      },
    }, "Pick by section →"));
    view.appendChild(actions);
  }

  // ---- Score profile improvement plan ----
  const profile = loadScoreProfile();
  if (profile?.analysis && profile.analysis.test === state.test) {
    const a = profile.analysis;
    const planCard = el("div", { class: "dash-card dash-plan" });
    planCard.appendChild(el("div", { class: "dash-card-label" }, "Your improvement plan"));
    const head = el("div", { class: "dash-plan-head" });
    head.appendChild(el("div", { class: "dash-plan-score" },
      el("div", { class: "dash-plan-score-current" }, `${a.overall_score}`),
      el("div", { class: "dash-plan-score-arrow" }, "→"),
      el("div", { class: "dash-plan-score-target" }, `${a.target?.overall ?? a.overall_score}`),
      el("div", { class: "dash-plan-score-meta" }, `target in ${a.target?.timeline_weeks ?? "?"} weeks`),
    ));
    head.appendChild(el("div", { class: "dash-plan-skills" },
      ...(a.skills || []).map((s) =>
        el("div", { class: `dash-plan-skill level-${s.level}` },
          el("div", { class: "dash-plan-skill-name" }, s.name),
          el("div", { class: "dash-plan-skill-score" }, String(s.score)),
        )
      ),
    ));
    planCard.appendChild(head);
    if (a.summary) {
      planCard.appendChild(el("div", { class: "dash-plan-summary" }, a.summary));
    }
    if (Array.isArray(a.plan) && a.plan.length) {
      planCard.appendChild(el("div", { class: "dash-plan-steps-label" }, "Recommended next steps"));
      const steps = el("ol", { class: "dash-plan-steps" });
      a.plan.forEach((step) => steps.appendChild(el("li", null, step)));
      planCard.appendChild(steps);
    }
    const planActions = el("div", { class: "dash-plan-actions" });
    planActions.appendChild(el("a", {
      href: "#",
      class: "dash-plan-update",
      onclick: (e) => { e.preventDefault(); $("#settings-nav").click(); },
    }, "Update score profile →"));
    planCard.appendChild(planActions);
    view.appendChild(planCard);
  }

  // ---- Mock Exam card ----
  const mockCard = el("div", { class: "dash-card dash-mock" });
  mockCard.appendChild(el("div", { class: "dash-card-label" }, "Mock exam"));
  mockCard.appendChild(el("div", { class: "dash-mock-text" },
    `Take a timed simulation of one section. No AI hints, no tips — just you and the clock, like the real ${TEST_LABELS[state.test]?.short || "PTE"}.`
  ));
  const mockBtns = el("div", { class: "dash-mock-btns" });
  const cfg = MOCK_CONFIGS[state.test] || {};
  for (const [section, sectionCfg] of Object.entries(cfg)) {
    const mins = Math.round(sectionCfg.durationSec / 60);
    const btn = el("button", {
      class: "ghost dash-mock-btn",
      onclick: () => {
        if (confirm(`Start ${TEST_LABELS[state.test]?.short || "PTE"} ${sectionCfg.label} mock?\n\n• ${sectionCfg.count} questions\n• ${mins} minute time limit\n• No tips or AI hints during the test\n• Score breakdown at the end`)) {
          startMockExam(state.test, section);
        }
      },
    },
      el("div", { class: "dash-mock-btn-title" }, sectionCfg.label),
      el("div", { class: "dash-mock-btn-meta" }, `${sectionCfg.count} Qs · ${mins} min`),
    );
    mockBtns.appendChild(btn);
  }
  mockCard.appendChild(mockBtns);
  view.appendChild(mockCard);

  // ---- Two-column grid: section accuracy + activity heatmap ----
  const cols = el("div", { class: "dash-cols" });

  // Section accuracy bars
  const sectionCard = el("div", { class: "dash-card" });
  sectionCard.appendChild(el("div", { class: "dash-card-label" }, "Accuracy by section"));
  if (Object.keys(stats.bySection).length === 0) {
    sectionCard.appendChild(el("div", { class: "dash-empty" }, "Practice your first question to see stats here."));
  } else {
    const bars = el("div", { class: "dash-bars" });
    const sectionOrder = ["reading", "listening", "writing", "speaking"];
    for (const sec of sectionOrder) {
      const s = stats.bySection[sec];
      if (!s) continue;
      bars.appendChild(makeBar(
        sec.charAt(0).toUpperCase() + sec.slice(1),
        s.correct, s.total
      ));
    }
    sectionCard.appendChild(bars);
  }
  cols.appendChild(sectionCard);

  // 30-day activity heatmap
  const heatCard = el("div", { class: "dash-card" });
  heatCard.appendChild(el("div", { class: "dash-card-label" }, "Last 30 days"));
  heatCard.appendChild(makeHeatmap(stats.dailyCounts));
  cols.appendChild(heatCard);

  view.appendChild(cols);

  // ---- Topic mastery ----
  if (Object.keys(stats.topicAccuracy).length > 0) {
    const masteryCard = el("div", { class: "dash-card" });
    masteryCard.appendChild(el("div", { class: "dash-card-label" }, "Topic mastery"));
    const list = el("div", { class: "dash-mastery-list" });
    const topics = Object.entries(stats.topicAccuracy)
      .filter(([_, t]) => t.total >= 2)
      .sort((a, b) => b[1].accuracy - a[1].accuracy)
      .slice(0, 8);
    for (const [topic, t] of topics) {
      const masteryClass = t.accuracy >= 80 ? "mastered" : t.accuracy >= 60 ? "progressing" : "weak";
      list.appendChild(el("div", { class: `dash-mastery-row ${masteryClass}` },
        el("div", { class: "dash-mastery-topic" }, topic),
        el("div", { class: "dash-mastery-meta" }, `${t.accuracy}% · ${t.total}`),
      ));
    }
    masteryCard.appendChild(list);
    view.appendChild(masteryCard);
  }

  // ---- Empty state for brand new users ----
  if (stats.totalAttempts === 0) {
    const empty = el("div", { class: "dash-card dash-onboarding" });
    empty.appendChild(el("div", { class: "dash-card-label" }, "Getting started"));
    empty.appendChild(el("div", { class: "dash-onboarding-text" },
      "Click any section in the top nav to pick a task type and start practicing. Wrong answers come with explanations and AI-powered follow-up questions to confirm you've actually learned."
    ));
    const ctas = el("div", { class: "dash-actions-row" });
    ctas.appendChild(el("button", {
      class: "primary dash-action-btn",
      onclick: () => {
        $$(".section-btn[data-section]").forEach((b) =>
          b.classList.toggle("active", b.dataset.section === "reading"));
        $("#home-nav").classList.remove("active");
        state.section = "reading";
        renderPicker();
      },
    }, "Start with Reading →"));
    empty.appendChild(ctas);
    view.appendChild(empty);
  }
}

function makeStat(value, label, extraClass = "") {
  return el("div", { class: `dash-stat ${extraClass}` },
    el("div", { class: "dash-stat-value" }, String(value)),
    el("div", { class: "dash-stat-label" }, label),
  );
}

function makeBar(label, num, total) {
  const pct = total > 0 ? Math.round((num / total) * 100) : 0;
  const tone = pct >= 80 ? "good" : pct >= 60 ? "ok" : "weak";
  return el("div", { class: "dash-bar-row" },
    el("div", { class: "dash-bar-label" }, label),
    el("div", { class: "dash-bar-track" },
      el("div", { class: `dash-bar-fill ${tone}`, style: `width: ${pct}%` })
    ),
    el("div", { class: "dash-bar-value" }, total > 0 ? `${pct}% (${num}/${total})` : "—"),
  );
}

function makeHeatmap(dailyCounts) {
  const wrap = el("div", { class: "dash-heatmap" });
  const today = new Date();
  for (let i = 29; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    const dateKey = d.toISOString().slice(0, 10);
    const count = dailyCounts[dateKey] || 0;
    const level = count === 0 ? 0 : count < 3 ? 1 : count < 7 ? 2 : count < 15 ? 3 : 4;
    const cell = el("div", {
      class: `dash-heat-cell level-${level}`,
      title: `${dateKey}: ${count} question${count === 1 ? "" : "s"}`,
    });
    wrap.appendChild(cell);
  }
  return wrap;
}

function computeStats() {
  const p = loadProgress();
  // Filter to current test only. For historical attempts without a test
  // field, infer from qid prefix ('i-' = ielts, otherwise pte).
  const attempts = (p.attempts || []).filter((a) => {
    const t = a.test || (String(a.qid || "").startsWith("i-") ? "ielts" : "pte");
    return t === state.test;
  });
  const today = new Date().toISOString().slice(0, 10);

  const stats = {
    totalAttempts: attempts.length,
    todayAttempts: 0,
    todayAccuracy: 0,
    overallAccuracy: 0,
    dailyStreak: 0,
    dueCount: 0,
    bySection: {},      // {section: {correct, total}}
    byType: {},         // {type: {section, correct, total}}
    topicAccuracy: {},  // {topic: {correct, total, accuracy}}
    dailyCounts: {},    // {YYYY-MM-DD: count}
    weakestType: null,
  };

  let totalCorrect = 0;
  let todayCorrect = 0;
  for (const a of attempts) {
    const date = new Date(a.ts).toISOString().slice(0, 10);
    stats.dailyCounts[date] = (stats.dailyCounts[date] || 0) + 1;
    if (date === today) {
      stats.todayAttempts += 1;
      if (a.correct) todayCorrect += 1;
    }
    if (a.correct) totalCorrect += 1;
    // by section
    if (!stats.bySection[a.section]) stats.bySection[a.section] = { correct: 0, total: 0 };
    stats.bySection[a.section].total += 1;
    if (a.correct) stats.bySection[a.section].correct += 1;
    // by type
    if (!stats.byType[a.type]) stats.byType[a.type] = { section: a.section, correct: 0, total: 0 };
    stats.byType[a.type].total += 1;
    if (a.correct) stats.byType[a.type].correct += 1;
    // by topic
    const topicKey = a.topic || "(general)";
    if (!stats.topicAccuracy[topicKey]) stats.topicAccuracy[topicKey] = { correct: 0, total: 0, accuracy: 0 };
    stats.topicAccuracy[topicKey].total += 1;
    if (a.correct) stats.topicAccuracy[topicKey].correct += 1;
  }

  stats.overallAccuracy = stats.totalAttempts > 0
    ? Math.round((totalCorrect / stats.totalAttempts) * 100) : 0;
  stats.todayAccuracy = stats.todayAttempts > 0
    ? Math.round((todayCorrect / stats.todayAttempts) * 100) : 0;

  // Topic accuracy %
  for (const t of Object.values(stats.topicAccuracy)) {
    t.accuracy = Math.round((t.correct / t.total) * 100);
  }

  // Find weakest type (lowest accuracy with at least 3 attempts)
  let weakest = null;
  for (const [type, t] of Object.entries(stats.byType)) {
    if (t.total < 3) continue;
    const acc = Math.round((t.correct / t.total) * 100);
    if (!weakest || acc < weakest.accuracy) {
      weakest = { type, section: t.section, accuracy: acc };
    }
  }
  stats.weakestType = weakest;

  // Daily streak: count consecutive days back from today with at least one attempt
  let streak = 0;
  const cursor = new Date();
  for (let i = 0; i < 365; i++) {
    const key = cursor.toISOString().slice(0, 10);
    if (stats.dailyCounts[key]) {
      streak += 1;
      cursor.setDate(cursor.getDate() - 1);
    } else {
      // Today missing? Don't break streak yet (give until end of day)
      if (i === 0) {
        cursor.setDate(cursor.getDate() - 1);
        continue;
      }
      break;
    }
  }
  stats.dailyStreak = streak;

  // Due count from SR queue
  stats.dueCount = dueQuestionIds().length;

  return stats;
}

// ============================================================================
// MOCK EXAM MODE — timed sequence of questions, no AI hints during the test
// ============================================================================
function startMockExam(test, section) {
  const cfg = MOCK_CONFIGS[test]?.[section];
  if (!cfg) return alert("Mock exam not configured for that section yet.");
  const pool = currentQuestions().filter((q) => q.section === section);
  if (pool.length === 0) return alert(`No ${section} questions available for this test.`);
  // Shuffle and take up to count
  const shuffled = pool.slice().sort(() => Math.random() - 0.5);
  const queue = shuffled.slice(0, Math.min(cfg.count, pool.length));
  state.mockExam = {
    active: true,
    test,
    section,
    label: cfg.label,
    queue,
    index: 0,
    startTs: Date.now(),
    durationSec: cfg.durationSec,
    results: [],
    timerInterval: null,
  };
  nextMockQuestion();
}

function nextMockQuestion() {
  const m = state.mockExam;
  if (!m) return;
  if (m.index >= m.queue.length) {
    return finishMockExam();
  }
  const q = m.queue[m.index];
  // Capture the BEFORE attempts count so we can know per-question outcome
  m._beforeAttempts = (loadProgress().attempts || []).length;
  renderQuestion(q);
  // Add a banner on the card showing mock progress + timer
  setTimeout(() => decorateMockBanner(), 0);
  startMockTimer();
}

function decorateMockBanner() {
  const m = state.mockExam;
  if (!m) return;
  const card = $("#card");
  if (!card) return;
  // Remove any prior mock banner
  card.querySelectorAll(".mock-banner").forEach((b) => b.remove());
  const banner = el("div", { class: "mock-banner" },
    el("div", { class: "mock-banner-left" },
      el("span", { class: "mock-pill" }, `MOCK EXAM · ${m.label.toUpperCase()}`),
      el("span", { class: "mock-progress" }, `Question ${m.index + 1} of ${m.queue.length}`),
    ),
    el("div", { class: "mock-timer", id: "mock-timer" }, "—:—"),
  );
  card.insertBefore(banner, card.firstChild);
  updateMockTimerDisplay();
}

function startMockTimer() {
  const m = state.mockExam;
  if (!m) return;
  if (m.timerInterval) clearInterval(m.timerInterval);
  m.timerInterval = setInterval(() => {
    const remain = m.durationSec - Math.floor((Date.now() - m.startTs) / 1000);
    if (remain <= 0) {
      clearInterval(m.timerInterval);
      m.timerInterval = null;
      finishMockExam(/*timeout=*/ true);
      return;
    }
    updateMockTimerDisplay();
  }, 1000);
}

function updateMockTimerDisplay() {
  const m = state.mockExam;
  const t = document.getElementById("mock-timer");
  if (!m || !t) return;
  const remain = Math.max(0, m.durationSec - Math.floor((Date.now() - m.startTs) / 1000));
  const mm = Math.floor(remain / 60);
  const ss = remain % 60;
  t.textContent = `${String(mm).padStart(2, "0")}:${String(ss).padStart(2, "0")}`;
  t.classList.toggle("urgent", remain <= 60);
}

function advanceMock() {
  // Called by mock-aware feedback's Next button
  const m = state.mockExam;
  if (!m) return;
  const after = loadProgress().attempts || [];
  const justAttempted = after.slice(m._beforeAttempts || after.length);
  // Record per-question result + capture user's answer for later review
  if (justAttempted.length) {
    const last = justAttempted[justAttempted.length - 1];
    m.results.push({
      qid: last.qid,
      correct: last.correct,
      topic: last.topic,
      type: last.type,
      user_answer: last.user_answer,
    });
  } else {
    m.results.push({ qid: m.queue[m.index].id, correct: false, type: m.queue[m.index].type });
  }
  m.index += 1;
  nextMockQuestion();
}

function finishMockExam(timeout = false) {
  const m = state.mockExam;
  if (!m) return;
  if (m.timerInterval) clearInterval(m.timerInterval);
  // Pull any final attempt we may have missed
  const after = loadProgress().attempts || [];
  const justAttempted = after.slice(m._beforeAttempts || after.length);
  if (justAttempted.length && (!m.results.length || m.results[m.results.length - 1]?.qid !== justAttempted[justAttempted.length - 1].qid)) {
    const last = justAttempted[justAttempted.length - 1];
    m.results.push({ qid: last.qid, correct: last.correct, topic: last.topic, type: last.type });
  }
  state.mockExam = null;
  renderMockResults(m, timeout);
}

function renderMockResults(m, timeout) {
  $("#picker").classList.add("hidden");
  $("#card").classList.add("hidden");
  $("#feedback").classList.add("hidden");
  $("#tips").classList.add("hidden");
  $("#tips-view").classList.add("hidden");
  $("#settings-view").classList.add("hidden");
  $("#dashboard-view").classList.remove("hidden");
  const view = $("#dashboard-view");
  clear(view);

  const correct = m.results.filter((r) => r.correct).length;
  const total = m.queue.length;
  const accuracy = total > 0 ? Math.round((correct / m.results.length || 1) * 100) : 0;
  const elapsedSec = Math.min(m.durationSec, Math.floor((Date.now() - m.startTs) / 1000));
  const mins = Math.floor(elapsedSec / 60);

  view.appendChild(el("div", { class: "dash-hero" },
    el("h1", { class: "dash-greeting" }, timeout ? "Time's up" : "Mock complete"),
    el("div", { class: "dash-subtext" },
      `${m.label} mock — ${m.results.length}/${total} questions in ${mins} min · ${accuracy}% accuracy`),
  ));

  const summary = el("div", { class: "dash-card dash-today" });
  summary.appendChild(el("div", { class: "dash-card-label" }, "Result"));
  const grid = el("div", { class: "dash-today-grid" });
  grid.appendChild(makeStat(correct, "correct", "dash-stat-primary"));
  grid.appendChild(makeStat(m.results.length - correct, "wrong"));
  grid.appendChild(makeStat(total - m.results.length, "unanswered"));
  grid.appendChild(makeStat(`${mins}m`, "elapsed"));
  summary.appendChild(grid);
  view.appendChild(summary);

  // Per-question breakdown with clickable cells
  const breakdownCard = el("div", { class: "dash-card" });
  breakdownCard.appendChild(el("div", { class: "dash-card-label" }, "Per-question result"));
  breakdownCard.appendChild(el("div", { class: "mock-review-hint" },
    "Click any cell to review the question — see the right answer, the explanation, and an AI analysis of what went wrong."));
  const grid2 = el("div", { class: "mock-result-grid" });
  m.queue.forEach((q, i) => {
    const r = m.results[i];
    const status = r ? (r.correct ? "correct" : "wrong") : "skipped";
    const cell = el("div", {
      class: `mock-result-cell ${status}`,
      title: `Question ${i + 1}${q.topic ? " — " + q.topic : ""}\nClick to review`,
      onclick: () => renderMockReview(m, i),
    }, String(i + 1));
    grid2.appendChild(cell);
  });
  breakdownCard.appendChild(grid2);
  view.appendChild(breakdownCard);

  // Review panel placeholder — populated when a cell is clicked
  const reviewPanel = el("div", { id: "mock-review-panel", class: "dash-card hidden" });
  view.appendChild(reviewPanel);

  // Actions
  const actions = el("div", { class: "dash-actions-row" });
  actions.appendChild(el("button", { class: "primary", onclick: () => renderDashboardView() }, "Back to dashboard"));
  actions.appendChild(el("button", {
    class: "ghost",
    onclick: () => startMockExam(m.test, m.section),
  }, "Try another mock"));
  view.appendChild(actions);
}

// Inline review of one specific question from a finished mock
function renderMockReview(mock, idx) {
  const q = mock.queue[idx];
  const r = mock.results[idx];
  const status = r ? (r.correct ? "correct" : "wrong") : "skipped";
  const panel = $("#mock-review-panel");
  if (!panel) return;
  panel.classList.remove("hidden");
  clear(panel);

  // Highlight the active cell in the grid
  document.querySelectorAll(".mock-result-cell").forEach((c, i) => {
    c.classList.toggle("active", i === idx);
  });

  panel.appendChild(el("div", { class: "dash-card-label" },
    `Question ${idx + 1} of ${mock.queue.length} · ${status === "correct" ? "Correct" : status === "wrong" ? "Wrong" : "Skipped"}`));

  // Question content (truncated for long passages)
  const qHeading = el("div", { class: "mock-review-question" });
  if (q.passage) {
    qHeading.appendChild(el("div", { class: "passage", style: "margin-bottom: 12px;" },
      q.passage.length > 600 ? q.passage.slice(0, 600) + "…" : q.passage));
  }
  if (q.question) qHeading.appendChild(el("div", { class: "qprompt" }, q.question));
  if (q.statement) qHeading.appendChild(el("div", { class: "qprompt" },
    "Statement: ", el("em", null, q.statement)));
  if (q.prompt) qHeading.appendChild(el("div", { class: "qprompt", style: "white-space: pre-wrap;" }, q.prompt));
  if (q.audio_text && !q.passage) qHeading.appendChild(el("div", { class: "passage" }, q.audio_text));
  panel.appendChild(qHeading);

  // Correct answer display
  if (status !== "skipped" || q.answer != null) {
    const ans = answerDisplay(q);
    panel.appendChild(ans);
  }

  // Bank explanation
  if (q.explanation) {
    panel.appendChild(el("div", { class: "feedback-label" }, "Why"));
    panel.appendChild(el("div", { class: "feedback-explanation" }, q.explanation));
  }

  // Trap warning (only if wrong)
  if (status === "wrong" && q.trap) {
    panel.appendChild(el(
      "div",
      { class: "feedback-trap" },
      el("div", { class: "feedback-label" }, "Watch out for"),
      q.trap
    ));
  }

  // AI tips for this specific question (cached if anyone has seen it before)
  if (aiAvailable()) {
    const tipsBox = el("div", { class: "tailored-tips-box", style: "margin-top: 16px;" });
    tipsBox.appendChild(el("div", { class: "cat-label tailored-label" }, "Tips for this question"));
    tipsBox.appendChild(el("div", { class: "tailored-status" },
      el("span", { class: "spinner spinner-sm" }),
      document.createTextNode(" Loading tips...")
    ));
    panel.appendChild(tipsBox);
    requestTailoredTips(q, tipsBox);
  }

  // AI analysis of wrong answer (only when wrong)
  if (status === "wrong" && aiAvailable() && r) {
    const analyzeBox = el("div", { class: "feedback-analyze", style: "margin-top: 16px;" },
      el("div", { class: "feedback-label" }, "AI analysis of your answer"),
      el("div", { class: "analyze-status" },
        el("span", { class: "spinner spinner-sm" }),
        document.createTextNode(" Analyzing...")
      ),
    );
    panel.appendChild(analyzeBox);
    const userAnswer = r.user_answer != null
      ? r.user_answer
      : "(user picked an incorrect option — specific selection not retained)";
    requestAnalysis(q, userAnswer, analyzeBox);
  }

  // Close button
  const close = el("div", { class: "actions", style: "margin-top: 16px;" });
  close.appendChild(el("button", {
    class: "ghost",
    onclick: () => {
      panel.classList.add("hidden");
      document.querySelectorAll(".mock-result-cell").forEach((c) => c.classList.remove("active"));
    },
  }, "Close review"));
  panel.appendChild(close);

  panel.scrollIntoView({ behavior: "smooth", block: "start" });
}

function practiceDue() {
  const due = dueQuestionIds();
  if (!due.length) return;
  const qid = due[0];
  // Find the question in current test's seed bank
  const q = currentQuestions().find((x) => x.id === qid);
  if (q) {
    $$(".section-btn").forEach((b) => b.classList.remove("active"));
    $$(".section-btn[data-section]").forEach((b) =>
      b.classList.toggle("active", b.dataset.section === q.section));
    state.section = q.section;
    renderQuestion(q);
  } else {
    alert("Some due questions aren't in the current test's bank (maybe community-generated). Pick by section instead.");
  }
}

boot();
