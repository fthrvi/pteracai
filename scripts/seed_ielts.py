#!/usr/bin/env python3
"""Seed IELTS Academic content into bank.json (v2 schema).

Idempotent: skips items whose id already exists in the IELTS bank.

IELTS task types added:
  - mcq_single (Reading) — same schema as PTE
  - tfng (Reading) — True / False / Not Given (NEW renderer in app.js)
  - listening_sc (Listening sentence completion via TTS) — uses fib schema
  - essay (Writing Task 2) — same schema as PTE
  - task1 (Writing Task 1) — uses essay schema with different rubric

Plus IELTS-specific tips for each task type + exam-level overview.
"""
from __future__ import annotations
import json
from pathlib import Path

BANK = Path(__file__).parent.parent / "public" / "data" / "bank.json"


# --------------------------------------------------------------------------
# IELTS Tips — strict PTE-style structure (categories: Strategy/Time/Traps/Scoring/Tricks)
# --------------------------------------------------------------------------
IELTS_TIPS = {
    "exam": [
        {"cat": "Test Format", "tip": "IELTS Academic = 2h 45min total. Listening (30 min, 40 Qs) → Reading (60 min, 40 Qs) → Writing (60 min, 2 tasks) → Speaking (11-14 min, separate appointment). No break between Listening/Reading/Writing."},
        {"cat": "Test Format", "tip": "Listening: audio plays ONCE only across all 4 sections. You get 10 EXTRA minutes after audio ends to transfer answers to the official sheet — use them to check spelling."},
        {"cat": "Test Format", "tip": "Reading: 60 min for 40 Qs across 3 passages = ~20 min per passage. Strict timing — no extra minutes given."},
        {"cat": "Time Management", "tip": "Writing: spend 20 min on Task 1 (150 words), 40 min on Task 2 (250 words). Task 2 is worth 2/3 of your writing score — don't get stuck on Task 1."},
        {"cat": "Time Management", "tip": "In Reading, allocate ~1 min/question + 5 min to skim each passage. If a question takes >1.5 min, mark and skip — you can come back unlike PTE."},
        {"cat": "Scoring Strategy", "tip": "IELTS scores 1-9 in 0.5 band increments per skill, plus an overall band (rounded). Most universities want 6.5 or 7.0 overall, often 6.5 minimum per skill."},
        {"cat": "Scoring Strategy", "tip": "Each correct answer in Listening AND Reading scores 1 raw point out of 40. Conversion to band: 30/40 ≈ 7.0, 35/40 ≈ 8.0. No partial credit, no negative marking."},
        {"cat": "Scoring Strategy", "tip": "Writing is marked on: Task Achievement/Response (25%), Coherence & Cohesion (25%), Lexical Resource (25%), Grammatical Range & Accuracy (25%). Memorize these four."},
        {"cat": "Tricks", "tip": "Answer in CAPITALS for Listening + Reading transfers — eliminates ambiguity (b vs 6, l vs 1). Examiners explicitly say this is fine."},
        {"cat": "Tricks", "tip": "Listening transfer minutes: don't just copy — check spelling, plural/singular, articles. ~3 marks per test are gained or lost here."},
        {"cat": "Tricks", "tip": "Reading 'Matching Headings' is the slowest task — do it LAST in each passage. Banking time first by doing T/F/NG and MCQ pays off."},
        {"cat": "Tricks", "tip": "Writing Task 2 essay: aim for ~280 words, not 250. Under-length is heavily penalized; slightly over is fine and shows range."},
        {"cat": "Score Bands", "tip": "Band 7 = 'good user, occasional inaccuracies'. Band 8 = 'very good, only occasional unsystematic errors'. The leap from 7 → 8 is mostly Lexical Resource and Grammar Range, not Task Response."},
    ],
    "reading_mcq_single": [
        {"cat": "Strategy", "tip": "Skim the passage first (90 sec MAX), then read questions, then scan for answers. Don't read deeply first — you'll run out of time."},
        {"cat": "Strategy", "tip": "Question order USUALLY follows passage order. If Q4 is in para 2, Q5 is likely in para 2-3."},
        {"cat": "Strategy", "tip": "For 'main idea' / 'best title' Qs, the answer comes from the OVERALL passage, not one paragraph. Read intro + conclusion if available."},
        {"cat": "Traps", "tip": "Watch for paraphrased options — IELTS rarely uses passage wording verbatim. If an option quotes the passage directly, suspect a trap."},
        {"cat": "Traps", "tip": "Distractors often EXTEND a passage claim ('always', 'all', 'never'). The passage says 'often', the trap says 'always'."},
        {"cat": "Time", "tip": "~1 minute per MCQ. If stuck, eliminate 2 and guess — no penalty for wrong answers."},
        {"cat": "Scoring", "tip": "1 raw point per correct. No negative marking. ALWAYS answer something — blanks guarantee zero."},
    ],
    "reading_tfng": [
        {"cat": "Strategy", "tip": "TRUE = statement matches passage. FALSE = passage explicitly contradicts. NOT GIVEN = passage doesn't address this either way."},
        {"cat": "Strategy", "tip": "The hardest distinction is FALSE vs NOT GIVEN. Test: can you point to a specific passage sentence that contradicts the statement? If yes → FALSE. If you're inferring or the passage simply doesn't cover it → NOT GIVEN."},
        {"cat": "Strategy", "tip": "Statements follow passage order — once you find Q5's location, Q6 is downstream."},
        {"cat": "Strategy", "tip": "Look for qualifier words in the statement: 'always', 'only', 'most', 'some'. Match these EXACTLY against the passage. A statement saying 'all X are Y' is FALSE if the passage says 'most X are Y'."},
        {"cat": "Templates", "tip": "Decision script: (1) Find the topic in the passage. (2) If found and matches → TRUE. (3) If found and contradicts → FALSE. (4) If NOT found at all → NOT GIVEN. Apply mechanically."},
        {"cat": "Time", "tip": "T/F/NG should be the FASTEST task — ~45 seconds each. If you're hesitating >1 min, mark NOT GIVEN and move on (it's the most common answer when you're unsure)."},
        {"cat": "Traps", "tip": "Statements that say MORE than the passage = NOT GIVEN (not FALSE). Statements that say the OPPOSITE = FALSE. This distinction costs people 2-3 points per test."},
        {"cat": "Traps", "tip": "Common words can have different meanings — 'rare' in everyday speech vs 'rare' in scientific text. Match the passage's usage, not your assumption."},
        {"cat": "Tricks", "tip": "Statistically, T/F/NG answers are roughly evenly distributed (≈1/3 each) across a passage's questions. If you have 7 TRUEs in a row, recheck."},
        {"cat": "Tricks", "tip": "Write the answer in CAPS on your answer sheet: 'TRUE', 'FALSE', 'NOT GIVEN'. Abbreviations like 'T' or 'NG' may or may not be accepted depending on the examiner — full words are guaranteed safe."},
        {"cat": "Scoring", "tip": "1 raw point per correct. Strict — 'TURE' or 'FLASE' (misspellings) score zero. Triple-check spelling."},
    ],
    "listening_sc": [
        {"cat": "Strategy", "tip": "Sentence completion / fill-in-blanks — read the sentence with blanks BEFORE the audio plays. The 30 seconds before each section is critical prep time."},
        {"cat": "Strategy", "tip": "Predict the type of word needed: noun? number? adjective? Knowing this tunes your ear to listen for the right thing."},
        {"cat": "Strategy", "tip": "Audio plays ONCE. If you miss one, do NOT pause to think — keep tracking; you'll lose 3 subsequent answers otherwise."},
        {"cat": "Strategy", "tip": "Word LIMIT instructions matter: 'NO MORE THAN TWO WORDS' means 1 or 2 — three words = zero score even if right."},
        {"cat": "Time", "tip": "Use the 10 transfer minutes after Section 4 to: (1) fix spelling, (2) check plurals, (3) capitalize names, (4) re-check ALL word counts against the instructions."},
        {"cat": "Traps", "tip": "Distractors in audio: speakers often state a wrong answer first, then correct themselves ('it's at 4… actually no, 4:30'). Last number/word wins."},
        {"cat": "Traps", "tip": "Spelling errors = zero. Common: 'accommodation' (double c, double m), 'committee' (double m, double t, double e), 'noticeable' (keep the e)."},
        {"cat": "Tricks", "tip": "If you're sure you heard a number but can't recall, write 'XX' — at least you remember the slot. The 10 transfer minutes are for forensic reconstruction."},
        {"cat": "Scoring", "tip": "1 raw point per blank. Most-tested Listening task type. Drill spelling of high-frequency academic words: 'accommodation', 'beginning', 'environment', 'necessary', 'separate'."},
    ],
    "writing_task1": [
        {"cat": "Strategy", "tip": "150 words MINIMUM in 20 minutes. Describe what you see in the chart/graph/diagram. NO personal opinion, NO speculation about causes."},
        {"cat": "Strategy", "tip": "4-paragraph structure: (1) Introduction paraphrasing the prompt, (2) Overview of main trends/features (CRITICAL — Task Achievement requires this), (3) Detail paragraph 1, (4) Detail paragraph 2."},
        {"cat": "Strategy", "tip": "The OVERVIEW paragraph is the most important — examiners check for it explicitly. Use phrases like 'Overall, it is clear that...' / 'The most striking feature is...'."},
        {"cat": "Templates", "tip": "Intro: 'The [chart/graph/diagram] illustrates [what], during [period]. The figures are measured in [units].'"},
        {"cat": "Templates", "tip": "Overview: 'Overall, it is evident that [main trend 1]. Additionally, [main trend 2]. The most striking feature is [outlier or peak].'"},
        {"cat": "Templates", "tip": "Detail: 'In [year], [data point]. By [later year], this figure had risen/fallen to [data point], representing a [increase/decrease] of [amount].'"},
        {"cat": "Templates", "tip": "Change vocabulary: rose / climbed / surged / increased gradually / dropped / plummeted / dipped / fluctuated / remained stable / reached a peak of / hit a low of."},
        {"cat": "Time", "tip": "20 minutes total: 3 min plan, 14 min write, 3 min check. If you go over 22 min, force-end and move to Task 2 — Task 2 is worth 2x."},
        {"cat": "Traps", "tip": "Writing under 150 words = automatic Task Achievement penalty (caps at band 5). Count if you're unsure."},
        {"cat": "Traps", "tip": "Repeating the prompt's exact wording in your intro doesn't help — examiners want PARAPHRASE. 'shows' → 'illustrates', 'people' → 'individuals'."},
        {"cat": "Tricks", "tip": "If the chart has 5+ data series, pick the 2-3 most striking for detail paragraphs. You can't describe everything in 150 words — be selective."},
        {"cat": "Scoring", "tip": "Task 1 scored on: Task Achievement (covers all key features + overview), Coherence/Cohesion, Lexical Resource, Grammatical Range. Each ~25% of Task 1 score. Task 1 is 1/3 of total Writing score."},
    ],
    "writing_essay": [
        {"cat": "Strategy", "tip": "250 words MINIMUM in 40 minutes. Aim for 270-290 — under-length is harshly penalized."},
        {"cat": "Strategy", "tip": "Identify the question type: (1) Opinion (do you agree?), (2) Discussion (discuss both views + your opinion), (3) Problem/Solution, (4) Advantages/Disadvantages, (5) Two-Part Question. Each demands a different structure."},
        {"cat": "Strategy", "tip": "5-paragraph structure: Intro (with thesis) + 2-3 body paragraphs (one main idea each + example) + Conclusion (restate + final thought)."},
        {"cat": "Strategy", "tip": "Plan 5 min: write down your thesis + 2 main points + 1 example for each. Don't start writing without a plan — incoherent essays cap at band 6."},
        {"cat": "Templates", "tip": "Intro: 'It is often argued that [topic]. While some maintain that [view A], others contend that [view B]. This essay will [outline thesis].'"},
        {"cat": "Templates", "tip": "Body topic sentence: 'Firstly, [main idea]. For example, [specific real-world example]. This demonstrates that [link to thesis].'"},
        {"cat": "Templates", "tip": "Connectors to rotate: Furthermore, Moreover, Additionally, Consequently, As a result, Nevertheless, Conversely, In contrast, On the other hand."},
        {"cat": "Time", "tip": "40 min total: 5 min plan, 30 min write, 5 min proofread. Proofreading catches 2-3 grammar/spelling fixes that move your score 0.5 band."},
        {"cat": "Traps", "tip": "Memorized template phrases ('I am inclined to opine that...') flag your essay to examiners. Use templates as structure, NOT as canned sentences."},
        {"cat": "Traps", "tip": "Going off-topic = automatic Task Response penalty. Re-read the prompt every 5 minutes while writing."},
        {"cat": "Traps", "tip": "Repeated vocabulary = capped Lexical Resource score. Don't say 'important' five times — swap in 'significant', 'crucial', 'pivotal', 'paramount'."},
        {"cat": "Tricks", "tip": "Mention ONE specific real-world example per body paragraph (a country, a year, a study, a person). Generic claims lose Task Response points."},
        {"cat": "Tricks", "tip": "Use ONE complex sentence structure per paragraph (conditional, relative clause, inversion). Showcases Grammatical Range — directly scored."},
        {"cat": "Scoring", "tip": "Task 2 worth 2/3 of total Writing score. Scored on Task Response, Coherence/Cohesion, Lexical Resource, Grammatical Range — each 25%."},
        {"cat": "Scoring", "tip": "Band 7 essay = clear position, well-developed ideas, flexible vocabulary with occasional errors, mix of complex structures. That's the realistic target for most test-takers."},
    ],
}


# --------------------------------------------------------------------------
# IELTS Reading — Multiple Choice
# --------------------------------------------------------------------------
IELTS_MCQ = [
    {
        "id": "i-mcq-001",
        "section": "reading",
        "type": "mcq_single",
        "topic": "main idea identification",
        "passage": "The concept of biophilia, introduced by biologist E.O. Wilson in 1984, suggests that humans possess an innate tendency to seek connections with nature and other forms of life. Recent studies in environmental psychology have lent considerable support to this hypothesis, demonstrating measurable improvements in mood, cognition, and even physical health among individuals regularly exposed to natural environments. Hospital patients with views of trees recover faster, urban dwellers who walk in parks report reduced anxiety, and even brief exposure to indoor plants can lower blood pressure. However, critics argue that biophilia's predictive power is limited: most evidence is correlational rather than causal, and cultural variation in nature preferences suggests biological hardwiring may be overstated.",
        "question": "What is the writer's main point about biophilia?",
        "options": [
            "It has been conclusively proven by environmental psychologists.",
            "Evidence supports it, but methodological limitations remain.",
            "It applies more to urban dwellers than to rural populations.",
            "Cultural factors completely undermine the biophilia hypothesis.",
        ],
        "answer": 1,
        "explanation": "The passage presents both supporting evidence (hospital recovery, parks, blood pressure) AND limitations (correlational not causal, cultural variation). Option B captures this balanced framing. A overstates ('conclusively proven'), C is a fabricated comparison, D overstates the critic position ('completely undermine').",
        "trap": "A is tempting because the passage spends most of its words on supporting evidence — readers anchor on volume. But the final sentence is the writer's actual stance, and it's hedged.",
    },
    {
        "id": "i-mcq-002",
        "section": "reading",
        "type": "mcq_single",
        "topic": "detail identification",
        "passage": "The rise of microplastics in marine ecosystems represents one of the most pervasive yet poorly understood environmental challenges of the 21st century. Defined as plastic particles under 5mm in diameter, microplastics originate from two main sources: primary microplastics, manufactured at small sizes for use in cosmetics or industrial abrasives, and secondary microplastics, formed when larger plastic items degrade through UV exposure, wave action, and biological processes. While the visible accumulation of plastic waste on coastlines draws public attention, microplastics infiltrate marine food webs invisibly, having been documented in zooplankton, fish, and even the deepest ocean trenches. The implications for human health, given that fish are a primary protein source for over three billion people, remain a subject of active investigation.",
        "question": "According to the passage, secondary microplastics are formed when:",
        "options": [
            "They are manufactured intentionally for cosmetics.",
            "Marine animals ingest larger plastic items.",
            "Larger plastic items break down through environmental processes.",
            "They escape from coastal landfills into the ocean.",
        ],
        "answer": 2,
        "explanation": "The passage explicitly defines secondary microplastics as 'formed when larger plastic items degrade through UV exposure, wave action, and biological processes' — option C paraphrases this directly. A describes PRIMARY microplastics. B and D are plausible-sounding but not stated in the passage.",
        "trap": "Option A is the most common error because readers conflate 'primary' and 'secondary' — IELTS deliberately puts the wrong category right next to the right answer.",
    },
    {
        "id": "i-mcq-003",
        "section": "reading",
        "type": "mcq_single",
        "topic": "writer's view",
        "passage": "The traditional model of academic publishing — in which researchers submit papers to journals, peer reviewers volunteer their time, and final articles are placed behind paywalls — has come under increasing scrutiny in recent decades. Critics argue that the system effectively transfers publicly funded research into the hands of private publishers, who then charge universities and libraries substantial sums for access. Open-access alternatives have grown, but they too face criticisms: 'article processing charges' can shift the financial burden to authors, disadvantaging researchers from less wealthy institutions, and predatory journals undermine the credibility of the open-access model. A truly equitable system would require coordinated international policy, sustained funding for non-commercial publication infrastructure, and a cultural shift in how academic prestige is measured.",
        "question": "What does the writer suggest about the open-access publishing model?",
        "options": [
            "It has successfully replaced the traditional paywall system.",
            "It offers significant benefits with no substantial drawbacks.",
            "It addresses some problems but introduces new ones.",
            "It should be abandoned in favor of the traditional model.",
        ],
        "answer": 2,
        "explanation": "The writer presents open-access as PARTIAL progress: 'grown' (some success) but with criticisms (processing charges, predatory journals). Option C captures this balanced view. A overstates ('successfully replaced'), B contradicts the criticism noted, D is the opposite of the writer's stance.",
        "trap": "B is tempting if you skim and see 'have grown' positively. Always read the 'but' clause that follows in IELTS passages.",
    },
    {
        "id": "i-mcq-004",
        "section": "reading",
        "type": "mcq_single",
        "topic": "inference",
        "passage": "Recent archaeological discoveries in northern Spain have challenged longstanding assumptions about Neanderthal cognition. Cave paintings dated to over 64,000 years ago — predating the arrival of modern humans in Europe by at least 20,000 years — strongly suggest that Neanderthals were capable of symbolic representation, a cognitive ability previously thought to be unique to Homo sapiens. The findings, made possible by improved uranium-thorium dating techniques, have prompted re-examination of other ambiguous artifacts and have reignited debates about what distinguishes 'modern' cognitive abilities from those of our extinct relatives. Some researchers remain cautious, noting that dating methods can carry uncertainties; others argue that the evidence is sufficient to compel a fundamental revision of how we conceptualize Neanderthal capabilities.",
        "question": "What can be inferred from the passage about scholarly opinion on Neanderthal cognition?",
        "options": [
            "All researchers now agree Neanderthals had symbolic cognition.",
            "The new findings are considered insufficient to change views.",
            "There is ongoing debate, though many find the evidence compelling.",
            "Symbolic cognition was originally thought to be a Neanderthal trait.",
        ],
        "answer": 2,
        "explanation": "The passage notes BOTH cautious researchers AND those wanting fundamental revision — this is ongoing debate. C captures this. A overstates ('all'), B contradicts 'compel a fundamental revision', D reverses the original assumption (it was thought to be Homo sapiens-only).",
        "trap": "A and D both reverse a key claim in the passage. Read the qualifier words carefully: 'some...others...' signals genuine disagreement.",
    },
    {
        "id": "i-mcq-005",
        "section": "reading",
        "type": "mcq_single",
        "topic": "main idea identification",
        "passage": "For much of the 20th century, urban planning was dominated by the principle of zoning: separating residential, commercial, and industrial activities into distinct districts. While this approach reduced certain conflicts — factories no longer abutted family homes — it also created cities heavily dependent on cars, with long commutes between zones and stagnant streetscapes outside business hours. The 21st century has seen a return to mixed-use development, where apartments sit above shops, workplaces share blocks with cafés, and public spaces remain active across the day. Advocates point to research showing that mixed-use neighborhoods experience lower rates of crime, higher property values, and stronger community bonds. The challenge now lies in retrofitting cities built for the zoning era to accommodate this denser, more integrated vision.",
        "question": "What is the main argument of the passage?",
        "options": [
            "Zoning was a complete failure as an urban planning approach.",
            "Mixed-use development is a return to historical urban design after a zoning era.",
            "Car dependence is the most serious problem facing modern cities.",
            "The 21st century requires entirely new urban planning principles never seen before.",
        ],
        "answer": 1,
        "explanation": "The passage frames mixed-use as a 'return' to integration after zoning split things apart — option B captures this historical pivot. A overstates (zoning had benefits too — 'reduced certain conflicts'). C and D are details/extensions not the main idea.",
        "trap": "C is tempting because car dependence is discussed, but it's a SYMPTOM of zoning, not the main argument. Main idea questions reward the architecture of the argument, not a vivid detail.",
    },
    {
        "id": "i-mcq-006",
        "section": "reading",
        "type": "mcq_single",
        "topic": "detail identification",
        "passage": "The decline of pollinating insects globally has prompted urgent calls for action from ecologists and farmers alike. Bees, in particular, are responsible for pollinating approximately one-third of the food crops consumed by humans, including most fruits, nuts, and many vegetables. The causes of decline are multiple and interacting: widespread pesticide use, especially neonicotinoids, weakens bee immune systems; habitat loss reduces foraging opportunities; and the spread of parasites like the Varroa mite devastates managed honeybee colonies. Wild bees face additional pressures from climate change, which disrupts the synchronization between flowering plants and pollinator activity. Conservation strategies that focus on a single threat are unlikely to succeed; effective response requires coordinated action across agriculture, land management, and climate policy.",
        "question": "According to the passage, why are single-threat conservation strategies insufficient?",
        "options": [
            "Because pesticides are the most serious problem and dominate other concerns.",
            "Because the causes of bee decline are multiple and interacting.",
            "Because farmers refuse to cooperate with conservation programs.",
            "Because the Varroa mite cannot be controlled by any current method.",
        ],
        "answer": 1,
        "explanation": "The passage explicitly says causes are 'multiple and interacting' and 'effective response requires coordinated action across agriculture, land management, and climate policy' — option B paraphrases this. A picks out one cause; C and D are not mentioned in the passage.",
        "trap": "A overweights one cause (pesticides) because the passage discusses it first and at length. IELTS often makes the wrong answer the SALIENT detail and the right answer the STRUCTURAL one.",
    },
    {
        "id": "i-mcq-007",
        "section": "reading",
        "type": "mcq_single",
        "topic": "writer's purpose",
        "passage": "In recent years, several major cities have introduced 'congestion pricing' — charging drivers a fee to enter central districts during peak hours — as a tool to reduce traffic and improve air quality. London's scheme, launched in 2003, reduced traffic volume in the charging zone by 15% in its first year, and Stockholm's 2007 implementation saw a similar 20-25% drop. Critics argue that such fees disproportionately burden lower-income drivers who lack alternatives. Proponents respond that revenue is typically reinvested in public transit, which over time creates better options for everyone. The empirical record suggests that congestion pricing works as advertised in terms of reducing traffic, but its equity implications depend heavily on how revenues are spent.",
        "question": "What is the writer's primary purpose in this passage?",
        "options": [
            "To argue that congestion pricing should be implemented worldwide.",
            "To present evidence and the main debate around congestion pricing.",
            "To criticize cities that have implemented congestion pricing schemes.",
            "To explain the technical mechanisms of congestion pricing.",
        ],
        "answer": 1,
        "explanation": "The writer cites specific data (London 15%, Stockholm 20-25%), then presents both critic and proponent views, then concludes with a hedged assessment ('depends heavily'). This is balanced analysis, not advocacy. B captures it. A and C are too one-sided; D ignores the debate content.",
        "trap": "A is tempting if you focus on the positive statistics — but the writer's TONE is analytical not persuasive. Look for 'should' / 'must' for advocacy markers (absent here).",
    },
    {
        "id": "i-mcq-008",
        "section": "reading",
        "type": "mcq_single",
        "topic": "detail identification",
        "passage": "The phenomenon of 'language attrition' — the gradual loss of a first language by speakers who have moved to a region where it is not used — has attracted growing interest from linguists. Studies of immigrants in particular have shown that attrition is most pronounced in vocabulary, with grammar tending to remain more stable. However, age at immigration plays a crucial role: children who migrate before adolescence are far more likely to experience significant attrition, sometimes losing their first language entirely if not actively maintained. Adult immigrants typically retain their first language even after decades in a new linguistic environment, though they may experience subtle changes such as slower word retrieval or interference from the dominant language. These findings have implications for heritage language preservation in immigrant communities.",
        "question": "According to the passage, which aspect of language is most susceptible to attrition?",
        "options": [
            "Grammar and sentence structure.",
            "Vocabulary.",
            "Pronunciation and accent.",
            "Reading and writing ability.",
        ],
        "answer": 1,
        "explanation": "The passage states directly: 'attrition is most pronounced in vocabulary, with grammar tending to remain more stable.' Option B paraphrases this. A contradicts the passage, C and D are not mentioned.",
        "trap": "If you skim and only catch the word 'grammar', you may misremember it as the answer. Always read the FULL sentence — qualifiers like 'most pronounced' vs 'remain more stable' decide which aspect is which.",
    },
]


# --------------------------------------------------------------------------
# IELTS Reading — True / False / Not Given
# --------------------------------------------------------------------------
IELTS_TFNG = [
    {
        "id": "i-tfng-001",
        "section": "reading",
        "type": "tfng",
        "topic": "true false not given",
        "passage": "The domestication of the horse, occurring approximately 5,500 years ago on the steppes of Central Asia, fundamentally transformed human societies. Archaeological evidence from the Botai culture in modern-day Kazakhstan provides the earliest direct indications of horse husbandry, including milk residues on pottery and bit-wear on horse teeth. The mobility revolution that followed allowed peoples to traverse vast distances, accelerated the diffusion of languages, and reshaped warfare. However, the horse's introduction to the Americas occurred far later — Spanish explorers in the 16th century brought horses to a continent where the species had been extinct for over 10,000 years. Indigenous peoples of the Great Plains rapidly adopted horse-based culture, transforming their societies in less than two centuries.",
        "statement": "The earliest evidence of horse domestication has been found in Kazakhstan.",
        "answer": "true",
        "explanation": "The passage explicitly says the Botai culture 'in modern-day Kazakhstan provides the earliest direct indications of horse husbandry.' Direct match — TRUE.",
        "trap": "Don't second-guess on TRUE answers. If the passage states it clearly, the answer is TRUE — don't talk yourself into NOT GIVEN.",
    },
    {
        "id": "i-tfng-002",
        "section": "reading",
        "type": "tfng",
        "topic": "true false not given",
        "passage": "The domestication of the horse, occurring approximately 5,500 years ago on the steppes of Central Asia, fundamentally transformed human societies. Archaeological evidence from the Botai culture in modern-day Kazakhstan provides the earliest direct indications of horse husbandry, including milk residues on pottery and bit-wear on horse teeth. The mobility revolution that followed allowed peoples to traverse vast distances, accelerated the diffusion of languages, and reshaped warfare. However, the horse's introduction to the Americas occurred far later — Spanish explorers in the 16th century brought horses to a continent where the species had been extinct for over 10,000 years. Indigenous peoples of the Great Plains rapidly adopted horse-based culture, transforming their societies in less than two centuries.",
        "statement": "Horses were native to the Americas before the arrival of European explorers.",
        "answer": "false",
        "explanation": "The passage says the horse 'had been extinct for over 10,000 years' in the Americas before the Spanish brought them. The statement claims natives before Europeans — the passage explicitly contradicts. FALSE.",
        "trap": "If you read 'horses brought to the Americas by Spanish' and stop there, you might pick NOT GIVEN. But the EXTINCT clause directly contradicts the statement — that's FALSE territory, not NOT GIVEN.",
    },
    {
        "id": "i-tfng-003",
        "section": "reading",
        "type": "tfng",
        "topic": "true false not given",
        "passage": "The domestication of the horse, occurring approximately 5,500 years ago on the steppes of Central Asia, fundamentally transformed human societies. Archaeological evidence from the Botai culture in modern-day Kazakhstan provides the earliest direct indications of horse husbandry, including milk residues on pottery and bit-wear on horse teeth. The mobility revolution that followed allowed peoples to traverse vast distances, accelerated the diffusion of languages, and reshaped warfare. However, the horse's introduction to the Americas occurred far later — Spanish explorers in the 16th century brought horses to a continent where the species had been extinct for over 10,000 years. Indigenous peoples of the Great Plains rapidly adopted horse-based culture, transforming their societies in less than two centuries.",
        "statement": "The Botai culture was the first to use horses for chariot racing.",
        "answer": "not given",
        "explanation": "The passage mentions Botai's milk residues, bit-wear, and 'mobility revolution' generally — but says NOTHING about chariot racing specifically. Not contradicted, not confirmed = NOT GIVEN.",
        "trap": "It SOUNDS plausible because of 'mobility revolution', but plausibility ≠ stated. The classic NG trap: 'this seems likely given the passage' — but IELTS requires the passage to state it explicitly.",
    },
    {
        "id": "i-tfng-004",
        "section": "reading",
        "type": "tfng",
        "topic": "true false not given",
        "passage": "Coral reefs, often called the rainforests of the sea, support roughly a quarter of all marine species despite covering less than 1% of the ocean floor. Their decline has accelerated alarmingly in recent decades, driven primarily by rising sea temperatures, which cause the symbiotic algae living within coral tissues to be expelled — a process known as bleaching. Without these algae, corals cannot photosynthesize their primary food source and may starve within weeks. Ocean acidification, caused by absorbed atmospheric CO2, compounds the threat by weakening coral skeletons. Some reef systems show remarkable resilience: the Red Sea's corals tolerate temperatures 5°C higher than their Indo-Pacific cousins, suggesting genetic adaptation may offer routes to conservation.",
        "statement": "Coral bleaching is caused when corals lose the algae that live inside them.",
        "answer": "true",
        "explanation": "The passage states directly: 'rising sea temperatures, which cause the symbiotic algae living within coral tissues to be expelled — a process known as bleaching.' Direct paraphrase = TRUE.",
        "trap": "None significant — this is a clear TRUE. The trap on TRUE statements is overthinking. Trust the passage.",
    },
    {
        "id": "i-tfng-005",
        "section": "reading",
        "type": "tfng",
        "topic": "true false not given",
        "passage": "Coral reefs, often called the rainforests of the sea, support roughly a quarter of all marine species despite covering less than 1% of the ocean floor. Their decline has accelerated alarmingly in recent decades, driven primarily by rising sea temperatures, which cause the symbiotic algae living within coral tissues to be expelled — a process known as bleaching. Without these algae, corals cannot photosynthesize their primary food source and may starve within weeks. Ocean acidification, caused by absorbed atmospheric CO2, compounds the threat by weakening coral skeletons. Some reef systems show remarkable resilience: the Red Sea's corals tolerate temperatures 5°C higher than their Indo-Pacific cousins, suggesting genetic adaptation may offer routes to conservation.",
        "statement": "All coral species are equally vulnerable to rising sea temperatures.",
        "answer": "false",
        "explanation": "The passage gives a counter-example: 'the Red Sea's corals tolerate temperatures 5°C higher than their Indo-Pacific cousins'. This explicitly contradicts 'all...equally vulnerable'. FALSE.",
        "trap": "Statements with ALL / NONE / ALWAYS are FALSE traps — IELTS uses them when the passage gives any counter-example. Scan for absolute language and check the passage for ANY exception.",
    },
    {
        "id": "i-tfng-006",
        "section": "reading",
        "type": "tfng",
        "topic": "true false not given",
        "passage": "Coral reefs, often called the rainforests of the sea, support roughly a quarter of all marine species despite covering less than 1% of the ocean floor. Their decline has accelerated alarmingly in recent decades, driven primarily by rising sea temperatures, which cause the symbiotic algae living within coral tissues to be expelled — a process known as bleaching. Without these algae, corals cannot photosynthesize their primary food source and may starve within weeks. Ocean acidification, caused by absorbed atmospheric CO2, compounds the threat by weakening coral skeletons. Some reef systems show remarkable resilience: the Red Sea's corals tolerate temperatures 5°C higher than their Indo-Pacific cousins, suggesting genetic adaptation may offer routes to conservation.",
        "statement": "Restoration projects in the Red Sea have successfully revived bleached coral.",
        "answer": "not given",
        "explanation": "The passage mentions the Red Sea's heat tolerance and suggests 'genetic adaptation may offer routes to conservation' — but says NOTHING about restoration projects or successful revival. Not confirmed, not contradicted = NOT GIVEN.",
        "trap": "The passage's mention of 'conservation' might tempt you to TRUE. But 'may offer routes to' is suggestive future-tense; the statement claims existing successful restoration. The passage doesn't say this happened.",
    },
]


# --------------------------------------------------------------------------
# IELTS Listening — Sentence Completion (uses TTS at runtime, fib-shaped schema)
# Each sentence gives the audio_text (what's read aloud) and a parallel fill-in form.
# We piggyback on the existing 'wfd' renderer for now — IELTS sentence completion
# differs slightly but the UX is "listen and type".
# --------------------------------------------------------------------------
IELTS_WFD = [
    {
        "id": "i-wfd-001",
        "section": "listening",
        "type": "wfd",
        "topic": "academic dictation",
        "audio_text": "The library will be closed for refurbishment from the fifteenth of March.",
        "answer": "The library will be closed for refurbishment from the fifteenth of March.",
        "explanation": "Spell out 'fifteenth' (not '15th'). 'Refurbishment' has the silent middle 'b'. Check capital M on March.",
    },
    {
        "id": "i-wfd-002",
        "section": "listening",
        "type": "wfd",
        "topic": "academic dictation",
        "audio_text": "Please remember to bring your student identification card to the seminar.",
        "answer": "Please remember to bring your student identification card to the seminar.",
        "explanation": "'Identification' — long word, easy to misspell (i-den-ti-fi-ca-tion). 'Seminar' not 'seminer'.",
    },
    {
        "id": "i-wfd-003",
        "section": "listening",
        "type": "wfd",
        "topic": "academic dictation",
        "audio_text": "All submissions must include a fully completed cover sheet and bibliography.",
        "answer": "All submissions must include a fully completed cover sheet and bibliography.",
        "explanation": "'Submissions' (double s in middle). 'Bibliography' — bibl-i-o-graphy. 'Cover sheet' is two words.",
    },
    {
        "id": "i-wfd-004",
        "section": "listening",
        "type": "wfd",
        "topic": "academic dictation",
        "audio_text": "Tutorials for first-year students will be held on Tuesday and Thursday afternoons.",
        "answer": "Tutorials for first-year students will be held on Tuesday and Thursday afternoons.",
        "explanation": "'Tutorials' plural. 'First-year' hyphenated as a compound modifier. Capital T on Tuesday and Thursday. 'Afternoons' plural.",
    },
    {
        "id": "i-wfd-005",
        "section": "listening",
        "type": "wfd",
        "topic": "academic dictation",
        "audio_text": "The deadline for module enrolment has been extended until next Friday.",
        "answer": "The deadline for module enrolment has been extended until next Friday.",
        "explanation": "British 'enrolment' (one l in middle), American 'enrollment' (double l) — both accepted. 'Extended' not 'extented'.",
    },
    {
        "id": "i-wfd-006",
        "section": "listening",
        "type": "wfd",
        "topic": "academic dictation",
        "audio_text": "Accommodation in halls of residence is offered to most international students.",
        "answer": "Accommodation in halls of residence is offered to most international students.",
        "explanation": "'Accommodation' = THE classic spelling trap (double c, double m). 'Halls of residence' is the British university term for dormitories.",
    },
    {
        "id": "i-wfd-007",
        "section": "listening",
        "type": "wfd",
        "topic": "academic dictation",
        "audio_text": "The committee will announce the successful candidates by the end of October.",
        "answer": "The committee will announce the successful candidates by the end of October.",
        "explanation": "'Committee' — double m, double t, double e. 'Successful' — two s's, two c's (sucCESSful). Capital O on October.",
    },
    {
        "id": "i-wfd-008",
        "section": "listening",
        "type": "wfd",
        "topic": "academic dictation",
        "audio_text": "Students are advised to consult their personal tutor before changing modules.",
        "answer": "Students are advised to consult their personal tutor before changing modules.",
        "explanation": "'Advised' (verb, d) not 'advice' (noun, c). 'Personal' not 'personel'. 'Modules' plural.",
    },
]


# --------------------------------------------------------------------------
# IELTS Writing Task 2 — Essays
# --------------------------------------------------------------------------
IELTS_ESSAYS = [
    ("opinion", "Some people believe that universities should focus on developing students' professional skills, while others argue that the main purpose of a university education is to develop knowledge for its own sake. Discuss both views and give your own opinion."),
    ("agree-disagree", "In many countries, the number of animal and plant species is decreasing rapidly. What do you think are the causes of this? What measures can be taken to address the problem?"),
    ("agree-disagree", "Some people think that international tourism is a positive development for all countries involved. Others believe its negative impacts outweigh its benefits. Discuss both views and give your own opinion."),
    ("problem-solution", "In many cities, traffic congestion has become a serious problem. What are the main causes of traffic congestion in cities, and what solutions would you propose?"),
    ("opinion", "Some people believe that governments should ban dangerous sports, while others think people should be allowed to take part in any sport of their choice. Discuss both views and give your opinion."),
    ("agree-disagree", "Online learning has become increasingly popular in recent years. Do the advantages of online learning outweigh the disadvantages?"),
    ("agree-disagree", "Some people think the best way to reduce crime is to give longer prison sentences. Others, however, believe there are better alternative methods. Discuss both views and give your opinion."),
    ("opinion", "In many countries, fast food is becoming cheaper and more widely available. Do the disadvantages of this outweigh the advantages?"),
    ("problem-solution", "Many young people today struggle with mental health issues such as anxiety and depression. What are the main causes of this trend, and what can governments and societies do to help?"),
    ("two-part", "Many museums charge for admission while others are free. Do you think the advantages of charging people for admission to museums outweigh the disadvantages?"),
]


# --------------------------------------------------------------------------
# IELTS Writing Task 1 — Visual description prompts
# (Stored using 'essay' type with task1 rubric since we don't have chart images)
# --------------------------------------------------------------------------
IELTS_TASK1 = [
    ("line graph",
     "The line graph below shows the percentage of households owning four different consumer goods (television, washing machine, refrigerator, and mobile phone) in a developing country between 1990 and 2020. Summarise the information by selecting and reporting the main features, and make comparisons where relevant. Write at least 150 words."),
    ("bar chart",
     "The bar chart shows the average hours per week that adults in five different countries (UK, USA, Germany, Japan, and Australia) spent on three leisure activities (reading, watching TV, and using social media) in 2020. Summarise the information by selecting and reporting the main features, and make comparisons where relevant. Write at least 150 words."),
    ("pie chart",
     "The pie charts compare the sources of energy used to generate electricity in a country in 1990 and 2020. The four sources are coal, natural gas, nuclear, and renewables. Summarise the information by selecting and reporting the main features, and make comparisons where relevant. Write at least 150 words."),
    ("process diagram",
     "The diagram below shows the process by which recycled paper is produced from used newspapers, magazines, and office paper. Summarise the information by selecting and reporting the main features. Write at least 150 words."),
    ("map",
     "The maps below show the village of Stokeford in 1930 and in 2020. Summarise the information by selecting and reporting the main features, and make comparisons where relevant. Write at least 150 words."),
]


def build():
    raw = json.loads(BANK.read_text())
    if raw.get("schema") != 2:
        print("ERROR: bank is not v2. Run migrate_bank_v2.py first.")
        return

    ielts = raw["tests"].setdefault("ielts", {"label": "IELTS Academic", "short": "IELTS", "tips": {}, "questions": []})
    ielts.setdefault("tips", {})
    ielts.setdefault("questions", [])

    existing_ids = {q["id"] for q in ielts["questions"]}
    added = 0

    # Tips: overwrite (single source of truth)
    ielts["tips"] = IELTS_TIPS

    # MCQ
    for q in IELTS_MCQ:
        if q["id"] in existing_ids:
            continue
        ielts["questions"].append(q)
        added += 1

    # T/F/NG
    for q in IELTS_TFNG:
        if q["id"] in existing_ids:
            continue
        ielts["questions"].append(q)
        added += 1

    # Listening WFD (sentence completion via dictation for now)
    for q in IELTS_WFD:
        if q["id"] in existing_ids:
            continue
        ielts["questions"].append(q)
        added += 1

    # Writing Task 2 essays
    for i, (topic, prompt) in enumerate(IELTS_ESSAYS):
        qid = f"i-essay-{100+i:03d}"
        if qid in existing_ids:
            continue
        ielts["questions"].append({
            "id": qid,
            "section": "writing",
            "type": "essay",
            "topic": topic,
            "prompt": prompt + " Write at least 250 words.",
            "rubric": "250-300 words. 5 paragraphs. Address the question type (opinion / discuss both / problem-solution / advantages-disadvantages / two-part) explicitly. Mark on Task Response, Coherence/Cohesion, Lexical Resource, Grammar.",
            "grading_notes": "IELTS Writing Task 2 scored on 4 criteria (each 25%): Task Response (addresses prompt fully + clear position + developed ideas), Coherence/Cohesion (organization + linking), Lexical Resource (vocab range + accuracy), Grammar (range + accuracy). Band 7 = clear position, well-developed ideas, flexible vocab with occasional errors, mix of complex structures.",
        })
        added += 1

    # Writing Task 1
    for i, (chart_type, prompt) in enumerate(IELTS_TASK1):
        qid = f"i-task1-{100+i:03d}"
        if qid in existing_ids:
            continue
        ielts["questions"].append({
            "id": qid,
            "section": "writing",
            "type": "task1",
            "topic": chart_type,
            "prompt": prompt,
            "rubric": "150+ words. 4 paragraphs: Intro (paraphrase prompt) + Overview (main trends, no detail) + 2 Detail paragraphs. NO opinion, NO speculation about causes. Use change vocabulary (rose / climbed / plummeted / fluctuated). Compare key data points.",
            "grading_notes": "IELTS Writing Task 1 scored on 4 criteria (each 25%): Task Achievement (covers all key features + clear overview), Coherence/Cohesion, Lexical Resource, Grammatical Range. The Overview paragraph is CRITICAL — examiners look for it explicitly. Without it, Task Achievement caps at band 5.",
        })
        added += 1

    BANK.write_text(json.dumps(raw, indent=2, ensure_ascii=False))
    return added, len(ielts["questions"])


if __name__ == "__main__":
    added, total = build()
    print(f"Added {added} IELTS questions. IELTS bank now has {total} questions total.")
