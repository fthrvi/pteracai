#!/usr/bin/env python3
"""Expansion v5 — listening depth.

PTE Listening additions:
  - lst_mcq: 6 Multiple Choice Single (Listening) — TTS plays a passage, then MCQ
  - lst_summary: 5 Summarize Spoken Text — TTS plays, user writes 50-70 word summary

IELTS Listening additions:
  - lst_sc: 6 Sentence Completion — TTS plays passage, user fills in blanks
    in a printed sentence (different schema from dictation)

Plus tips for the new listening task types.
"""
from __future__ import annotations
import json
from pathlib import Path

BANK = Path(__file__).parent.parent / "public" / "data" / "bank.json"


PTE_LST_MCQ = [
    {
        "topic": "academic lecture",
        "audio_text": "Today's lecture focuses on the impact of urbanization on biodiversity. As cities expand, they fragment habitats and reduce the connectivity that many species depend on for migration and genetic exchange. Studies in five major metropolitan areas have shown that bird species diversity drops sharply within the urban core, though some species — like crows, pigeons, and certain raptors — actually thrive in these environments. The lesson for urban planners is that thoughtful design, including green corridors that connect parks, can substantially reduce the biodiversity cost of urban growth.",
        "question": "What does the lecturer suggest can reduce the biodiversity impact of urban growth?",
        "options": [
            "Stopping all urban expansion immediately.",
            "Designing green corridors that connect park spaces.",
            "Removing all species that don't thrive in cities.",
            "Building taller buildings to reduce city footprint.",
        ],
        "answer": 1,
        "explanation": "The lecturer explicitly says 'green corridors that connect parks, can substantially reduce the biodiversity cost'. Option B paraphrases this. A is extreme, C contradicts the lecture's nuanced view, D isn't mentioned.",
        "trap": "Option D ('taller buildings') sounds like good urban planning but isn't in the lecture. Stick to what's explicitly said.",
    },
    {
        "topic": "academic lecture",
        "audio_text": "Sleep researchers have demonstrated that memory consolidation occurs preferentially during specific stages of sleep, with deep slow-wave sleep being most important for fact and event memories, while REM sleep appears critical for emotional processing and creative problem-solving. This is why cutting sleep short by even an hour can disproportionately impair the type of learning that depends on REM, which is concentrated in the later half of the night. Students who pull all-nighters before exams may retain some surface material but typically perform worse on tasks requiring deeper integration of what they've learned.",
        "question": "According to the lecturer, why are all-nighters particularly counterproductive for students?",
        "options": [
            "Because they completely eliminate the ability to remember any information.",
            "Because they disproportionately impair deeper learning that depends on REM sleep.",
            "Because they reduce the brain's ability to absorb new material at all.",
            "Because they damage long-term physical health.",
        ],
        "answer": 1,
        "explanation": "The lecturer says all-nighters affect 'tasks requiring deeper integration' and connects this to losing REM sleep. Option B captures this. A overstates ('completely'), C and D aren't said in the passage.",
        "trap": "A is the extreme version of what was said. IELTS/PTE distractors often take a hedged claim and make it absolute.",
    },
    {
        "topic": "academic lecture",
        "audio_text": "I want to introduce the concept of opportunity cost, which is fundamental to economic thinking. The opportunity cost of any choice is the value of the next best alternative you give up. For example, if you choose to spend an hour studying instead of working, the opportunity cost is the wages you would have earned. This concept is often invisible because it's about what you don't see — the path not taken. But ignoring opportunity costs leads to bad decisions. The discipline of asking 'what else could we be doing with these resources?' is at the heart of economic analysis.",
        "question": "What is the main point the lecturer is making about opportunity cost?",
        "options": [
            "It is the most expensive choice you could make.",
            "It's important precisely because it's often invisible in decision-making.",
            "It applies only to choices about money and wages.",
            "It is a concept used mostly in personal finance, not in business.",
        ],
        "answer": 1,
        "explanation": "The lecturer emphasizes opportunity cost is 'often invisible' and that ignoring it 'leads to bad decisions' — option B captures the importance + invisibility paradox. A misdefines it, C limits the scope wrongly, D narrows the application.",
        "trap": "C is tempting because the example given uses wages. But the lecturer presents it as broadly applicable, not money-only.",
    },
    {
        "topic": "academic lecture",
        "audio_text": "The history of antibiotics provides a striking example of both medical triumph and unintended consequence. Penicillin and its successors transformed bacterial infections from frequent killers into easily treatable conditions, dramatically extending life expectancy in the twentieth century. However, widespread use — and overuse — created selective pressure for resistant bacterial strains. Today, the World Health Organization considers antimicrobial resistance one of the most serious threats to global health, with researchers in a race to develop new antibiotics before existing ones become ineffective.",
        "question": "What is the speaker's overall argument about antibiotics?",
        "options": [
            "Antibiotics are no longer useful as a treatment for any infection.",
            "Antibiotics have been a major triumph but have created new problems through overuse.",
            "Antibiotics should be banned to prevent further resistance.",
            "Antibiotics are entirely safe and have no downsides.",
        ],
        "answer": 1,
        "explanation": "The lecturer presents BOTH the triumph and the resistance problem — option B captures this duality. A overstates, C is extreme, D contradicts.",
        "trap": "A and D are both extreme positions. The lecturer's argument is the balanced one in the middle — typical of academic speech.",
    },
    {
        "topic": "academic lecture",
        "audio_text": "In today's session we'll discuss confirmation bias, which is the human tendency to seek out, interpret, and remember information that confirms our existing beliefs. This bias affects everyone, regardless of intelligence or education, and explains many phenomena we observe in modern society — from political polarization to the spread of misinformation. Importantly, simply telling people about confirmation bias is rarely enough to overcome it. The most effective interventions involve structured techniques that force consideration of contrary evidence, such as deliberately seeking out the strongest case for opposing views.",
        "question": "According to the lecturer, what is the most effective response to confirmation bias?",
        "options": [
            "Educating people about its existence is usually sufficient.",
            "Avoiding all media that might present opposing views.",
            "Using structured techniques to force consideration of contrary evidence.",
            "Trusting that intelligent people don't suffer from this bias.",
        ],
        "answer": 2,
        "explanation": "The lecturer explicitly says 'most effective interventions involve structured techniques that force consideration of contrary evidence' — option C paraphrases this. A contradicts (the lecturer says education alone is rarely enough), B is the opposite of the recommendation, D contradicts the 'everyone' claim.",
        "trap": "A is what you might intuitively think (more awareness = solution) — but the lecturer specifically rebuts this. Active listening for refutations matters.",
    },
    {
        "topic": "academic lecture",
        "audio_text": "Recent advances in materials science have produced fabrics that can monitor health metrics like heart rate and respiration, generate small amounts of electricity from body motion, or even change color in response to temperature. These so-called smart textiles are moving from research labs into commercial products faster than many anticipated. Athletic apparel manufacturers are already integrating sensors into garments, and medical applications — particularly for elderly care monitoring — represent a substantial growth area. However, questions about durability through repeated washing, manufacturing scalability, and the lifecycle environmental impact remain open challenges.",
        "question": "What current challenges does the lecturer identify for smart textiles?",
        "options": [
            "The technology is decades away from being commercially viable.",
            "Durability through washing, manufacturing scale, and environmental impact.",
            "Smart textiles have been entirely rejected by the athletic industry.",
            "Only medical applications are practical; consumer use is impossible.",
        ],
        "answer": 1,
        "explanation": "The lecturer lists 'durability through repeated washing, manufacturing scalability, and the lifecycle environmental impact' as open challenges. Option B captures this. A contradicts ('moving from labs to products'), C and D contradict the lecturer's commercial-progress framing.",
        "trap": "A reverses the lecturer's actual claim that smart textiles are commercializing quickly.",
    },
]


PTE_LST_SUMMARY = [
    {
        "topic": "social science",
        "audio_text": "Today's lecture examines the rise of so-called gig economy work — short-term, contract-based employment mediated by digital platforms like Uber, DoorDash, and Upwork. Proponents argue that gig work offers flexibility and autonomy that traditional employment cannot match: workers choose when and how much to work, can simultaneously hold multiple positions, and avoid the rigidity of conventional office hours. Critics counter that this flexibility comes at significant cost — gig workers typically lack employer-provided health insurance, retirement contributions, paid sick leave, and the legal protections afforded to employees. They argue that what platforms present as worker freedom is in many cases a transfer of risk from employer to worker. Some jurisdictions have moved to reclassify gig workers as employees, while others have created intermediate legal categories. The honest assessment is that the gig economy is neither the unalloyed liberation its champions claim nor the exploitation its harshest critics describe. Its effects vary enormously by industry, by worker situation, and by what alternative employment is available. As policy and platform practice continue to evolve, the most productive question may not be 'is the gig economy good or bad?' but rather 'what specific reforms would let workers capture flexibility while restoring basic protections?'",
        "rubric": "50-70 words, ~10 minutes. Capture main claim + key tension. Use a complex structure.",
        "sample": "The lecturer argues that the gig economy is neither pure liberation nor exploitation, with platforms offering genuine flexibility but transferring traditional employment risks to workers, and recommends that the most productive policy question is how to preserve flexibility while restoring protections like health insurance and paid leave.",
    },
    {
        "topic": "history",
        "audio_text": "I want to discuss the long-term impact of the printing press on European society. When Johannes Gutenberg developed movable metal type around 1440, the immediate effect was making books cheaper to produce. Within fifty years, an estimated twenty million books had been printed in Europe. But the deeper consequences were less obvious at the time. Mass production of religious texts fueled the Protestant Reformation by allowing dissenting interpretations to spread faster than authorities could suppress them. The standardization of texts contributed to the standardization of national languages, which in turn helped consolidate the modern nation-state. Scientific exchange accelerated dramatically once researchers could read each other's work without relying on hand-copied manuscripts. The printing press also shifted political power: increased literacy gradually undermined elites whose authority had depended on controlling access to written knowledge. None of these effects were intended by Gutenberg himself, who died bankrupt and uncertain of his commercial success. The lesson is that transformative technologies often produce their largest effects through second- and third-order consequences that the inventors never anticipated.",
        "rubric": "50-70 words, ~10 minutes. Capture multiple impacts + the meta-lesson.",
        "sample": "The lecturer explains that the printing press's deepest impacts on European society were unintended, including fueling the Protestant Reformation, standardizing national languages and consolidating nation-states, accelerating scientific exchange, and undermining elite authority over knowledge, illustrating how transformative technologies often produce their largest effects through second- and third-order consequences inventors never anticipate.",
    },
    {
        "topic": "psychology",
        "audio_text": "Today we'll examine the concept of flow, introduced by psychologist Mihaly Csikszentmihalyi in the 1970s. Flow describes a particular psychological state in which a person is fully absorbed in an activity, losing awareness of time, self-consciousness, and surrounding distractions. Csikszentmihalyi identified several conditions that produce flow: clear goals, immediate feedback on performance, and an optimal challenge level — neither too easy, which produces boredom, nor too difficult, which produces anxiety. Flow has been studied across diverse activities — surgeons performing operations, athletes competing, musicians playing, programmers debugging — and consistently correlates with both high performance and reported wellbeing. Recent research has explored whether digital environments can be designed to induce flow, with mixed results: some structured tasks like puzzle games successfully achieve it, while many social media interfaces seem to produce the opposite — fragmented attention without absorption. The practical takeaway is that flow is most reliably accessible when we structure our work around clear, slightly challenging goals with rapid feedback, and when we deliberately minimize the kinds of interruption that pull us out of deep engagement.",
        "rubric": "50-70 words. Capture definition + conditions + practical implication.",
        "sample": "Csikszentmihalyi's concept of flow describes a state of full absorption with lost time awareness, produced by clear goals, immediate feedback, and an optimal challenge level between boredom and anxiety, and consistently correlates with both performance and wellbeing across activities, suggesting that workers should structure tasks around challenging-but-achievable goals and minimize interruptions that disrupt deep engagement.",
    },
    {
        "topic": "biology",
        "audio_text": "This morning's lecture covers the discovery and significance of mitochondria. These cellular organelles, found in nearly all eukaryotic cells, produce most of the energy that powers our biological activity through a process called cellular respiration. What makes mitochondria particularly interesting is their evolutionary origin: they were once free-living bacteria that were engulfed by larger cells about two billion years ago and gradually became permanent residents in a symbiotic relationship. This origin explains several of their unusual features — they have their own DNA, separate from the cell's nuclear genome; they reproduce independently when the cell divides; and they have a double membrane consistent with having once been engulfed by another cell. Modern medicine has come to recognize that mitochondrial dysfunction underlies a surprising range of human diseases, from rare inherited conditions to common problems like type 2 diabetes and various neurodegenerative disorders. The field of mitochondrial medicine is a growing area of research with potential implications for treatment across many conditions.",
        "rubric": "50-70 words. Capture function + evolutionary origin + medical relevance.",
        "sample": "The lecturer explains that mitochondria are cellular organelles that produce most of our energy and evolved from free-living bacteria engulfed by larger cells two billion years ago, with their distinct DNA, independent reproduction, and double membrane reflecting this origin, and notes that mitochondrial dysfunction underlies a surprising range of human diseases including diabetes and neurodegenerative disorders.",
    },
    {
        "topic": "economics",
        "audio_text": "Let's discuss the concept of network effects, which has become central to understanding why certain technology businesses dominate their markets. A network effect occurs when a product or service becomes more valuable as more people use it. The telephone is the classic early example: a single telephone is useless, two phones permit one conversation, but a network of millions of phones enables a vast web of communication. Modern digital platforms exhibit even stronger network effects. Social media platforms gain value as more friends join; marketplaces become more useful as more buyers and sellers participate; communication apps work better the more contacts use the same tool. These dynamics produce winner-take-all or winner-take-most outcomes that traditional market analysis struggles to explain. They also raise difficult policy questions about competition: standard antitrust frameworks assumed that high market share would eventually be eroded by competitors offering better products, but network effects can entrench dominant firms in ways that no superior alternative can easily displace. This is why regulators in the United States, the European Union, and elsewhere have begun reconsidering how competition law should apply to platform businesses.",
        "rubric": "50-70 words. Capture definition + examples + policy implication.",
        "sample": "The lecturer explains that network effects make products more valuable as more people use them, exemplified by telephones and modern digital platforms like social media and marketplaces, producing winner-take-all outcomes that entrench dominant firms in ways traditional competition law struggles to address, prompting regulators in the US, EU, and elsewhere to reconsider how antitrust frameworks should apply to platform businesses.",
    },
]


# IELTS Listening Sentence Completion (lst_sc):
# Schema: audio_text (played by TTS), text_parts (N+1 strings around N blanks),
# answer (array of strings — single words / short phrases). Different from
# reading 'fib' because user TYPES the blanks (no dropdown), and answers may
# be a few words long.
IELTS_LST_SC = [
    {
        "topic": "course registration",
        "audio_text": "Welcome to the orientation. Course registration opens on September fifteenth and closes at the end of the third week. Please remember to bring your student identification card to any meetings with your advisor. All textbooks for the first semester are available at the campus bookstore, which is located in the main building on the second floor.",
        "text_parts": [
            "Course registration opens on September ",
            " and closes at the end of the ",
            " week. Students must bring their ",
            " to meetings with advisors. Textbooks are available at the campus bookstore on the ",
            " floor of the main building.",
        ],
        "answer": ["fifteenth", "third", "student identification card", "second"],
    },
    {
        "topic": "library tour",
        "audio_text": "Welcome to the university library. We have over three hundred thousand books in our main collection, and you can borrow up to ten items at a time as an undergraduate, or twenty items as a postgraduate. Loans are normally for two weeks, but reference books cannot be borrowed at all. The library closes at midnight during term time, but only at six in the evening during vacation periods.",
        "text_parts": [
            "The library has over ",
            " books in the main collection. Undergraduates can borrow up to ",
            " items, postgraduates up to ",
            " items. Loans last for ",
            ", though reference books cannot be borrowed. The library closes at midnight in term time but at ",
            " during vacation.",
        ],
        "answer": ["three hundred thousand", "ten", "twenty", "two weeks", "six in the evening"],
    },
    {
        "topic": "field trip details",
        "audio_text": "The geology field trip will take place during the second week of October. Students should bring sturdy walking boots, waterproof clothing, and a notebook. The bus departs from the main entrance at seven thirty in the morning and returns by six in the evening. Lunch will not be provided, so please bring your own packed lunch.",
        "text_parts": [
            "The field trip is during the ",
            " of October. Students should bring sturdy walking boots, ",
            " clothing, and a ",
            ". The bus departs at ",
            " from the main entrance and returns by ",
            ". Bring your own ",
            ".",
        ],
        "answer": ["second week", "waterproof", "notebook", "seven thirty", "six in the evening", "packed lunch"],
    },
    {
        "topic": "assignment instructions",
        "audio_text": "For your first major assignment, you'll need to submit a research proposal of approximately two thousand words. The proposal must include a clear research question, a brief literature review, and a proposed methodology. Submissions are due by five o'clock on the Friday of the seventh week. Late submissions will be penalized at ten percent per day. Please upload your work to the course website.",
        "text_parts": [
            "The research proposal should be approximately ",
            " words and must include a clear research question, a brief literature review, and a proposed ",
            ". Submissions are due by ",
            " on the Friday of the ",
            ". Late submissions are penalized at ",
            " per day.",
        ],
        "answer": ["two thousand", "methodology", "five o'clock", "seventh week", "ten percent"],
    },
    {
        "topic": "accommodation options",
        "audio_text": "Student accommodation comes in three main forms. Halls of residence are the most common choice for first-year students, with costs ranging from one hundred and twenty to two hundred pounds per week, depending on whether you choose a shared bathroom or en-suite room. Private rental properties are more flexible but require a security deposit, usually equivalent to six weeks of rent. Homestay arrangements with local families are particularly popular with international students seeking to improve their English.",
        "text_parts": [
            "There are ",
            " main types of student accommodation. Halls of residence cost between ",
            " and two hundred pounds per week. Private rentals require a security deposit of usually ",
            " of rent. ",
            " arrangements are popular with international students seeking to improve their English.",
        ],
        "answer": ["three", "one hundred and twenty", "six weeks", "Homestay"],
    },
    {
        "topic": "career service",
        "audio_text": "The career service offers a range of support for students and recent graduates. Drop-in sessions for general advice run every Tuesday and Thursday afternoon between two and four. For longer one-to-one appointments, you must book at least one week in advance through the online system. We also organize an annual careers fair in March, where over fifty employers come to campus to meet potential candidates. The service is available to current students and to graduates for up to two years after leaving.",
        "text_parts": [
            "Drop-in advice runs every Tuesday and Thursday afternoon between ",
            ". One-to-one appointments require booking at least ",
            " in advance. The annual careers fair takes place in ",
            ", attended by over ",
            " employers. The service is available to graduates for ",
            " after leaving.",
        ],
        "answer": ["two and four", "one week", "March", "fifty", "two years"],
    },
]


LISTENING_TIPS = {
    "listening_lst_mcq": [
        {"cat": "Strategy", "tip": "Read all question options BEFORE the audio plays. The 30-second pre-audio window is your most important prep tool — pre-loaded context tunes your ear."},
        {"cat": "Strategy", "tip": "Identify keywords in each option (verbs, key nouns) and listen for synonyms in the audio. The correct option usually PARAPHRASES the audio rather than quoting it."},
        {"cat": "Time", "tip": "You can re-listen by clicking 'Play sentence' — but in the real exam, audio plays once. Practice with single play to build proper listening discipline."},
        {"cat": "Traps", "tip": "Distractor options often contain WORDS from the audio but misuse them (e.g., audio says 'X is uncommon', distractor says 'X is common')."},
        {"cat": "Tricks", "tip": "If two options seem to fit, choose the one that better captures the speaker's MAIN argument, not a side detail. Listen for stress and emphasis cues."},
    ],
    "listening_lst_summary": [
        {"cat": "Strategy", "tip": "Take notes during audio using keywords only. Don't write full sentences — capture topic, 2-3 main points, key examples."},
        {"cat": "Strategy", "tip": "50-70 words in ONE sentence isn't realistic — use 2-3 sentences that flow as a tight summary. The 50-70 constraint is on TOTAL words."},
        {"cat": "Templates", "tip": "Template: 'The lecturer argues that [main claim], explaining [key supporting points], and concludes that [implication or recommendation].'"},
        {"cat": "Time", "tip": "10 minutes total. Spend the first 90 seconds JUST listening, then 60 seconds organizing notes, then 6 minutes writing."},
        {"cat": "Traps", "tip": "Quoting the audio verbatim is dangerous — the AI grader rewards PARAPHRASE. Restate the lecturer's claim in your own words."},
        {"cat": "Scoring", "tip": "Dual-scored on LISTENING + WRITING. High-leverage task — drill summarize-spoken-text alongside SWT for compounding gains."},
    ],
    "listening_lst_sc": [
        {"cat": "Strategy", "tip": "Read the printed sentence FIRST, identifying what TYPE of word each blank needs (date? name? number? noun?). This dramatically improves your hit rate."},
        {"cat": "Strategy", "tip": "Don't worry about catching every word in the audio — focus on the specific data points your blanks need."},
        {"cat": "Strategy", "tip": "Word limit instructions matter: 'NO MORE THAN TWO WORDS' means one or two — three words = zero score even if right."},
        {"cat": "Traps", "tip": "Speakers may state a wrong answer first, then correct themselves ('it's at 4… actually no, 4:30'). Last value wins."},
        {"cat": "Traps", "tip": "Spelling matters: 'accommodation' (double c, double m), 'beginning' (double n), 'committee' (double m, double t, double e)."},
        {"cat": "Tricks", "tip": "If you miss a blank, write 'XX' to mark the slot, then come back. Don't let one missed item make you lose the next one."},
        {"cat": "Scoring", "tip": "Each blank is independent — partial credit applies. 4/6 correct = 67%."},
    ],
}


def build():
    raw = json.loads(BANK.read_text())
    if raw.get("schema") != 2:
        print("ERROR: not v2.")
        return 0, 0
    pte = raw["tests"]["pte"]
    ielts = raw["tests"]["ielts"]
    existing_pte_ids = {q["id"] for q in pte["questions"]}
    existing_ielts_ids = {q["id"] for q in ielts["questions"]}
    added_pte = 0
    added_ielts = 0

    # PTE Listening MCQ
    for i, q in enumerate(PTE_LST_MCQ):
        qid = f"l-mcq-{100+i:03d}"
        if qid in existing_pte_ids: continue
        pte["questions"].append({
            "id": qid, "section": "listening", "type": "lst_mcq",
            "topic": q["topic"], "audio_text": q["audio_text"],
            "question": q["question"], "options": q["options"], "answer": q["answer"],
            "explanation": q["explanation"], "trap": q.get("trap", ""),
        })
        added_pte += 1

    # PTE Listening Summarize Spoken Text
    for i, q in enumerate(PTE_LST_SUMMARY):
        qid = f"l-sst-{100+i:03d}"
        if qid in existing_pte_ids: continue
        pte["questions"].append({
            "id": qid, "section": "listening", "type": "lst_summary",
            "topic": q["topic"], "audio_text": q["audio_text"],
            "rubric": q["rubric"], "sample": q["sample"],
            "grading_notes": "Dual-scored on LISTENING + WRITING. Capture main claim + 2-3 supporting points in 50-70 words. AI grades transcript content; don't quote the audio verbatim.",
        })
        added_pte += 1

    # IELTS Listening Sentence Completion
    for i, q in enumerate(IELTS_LST_SC):
        qid = f"i-lst-sc-{100+i:03d}"
        if qid in existing_ielts_ids: continue
        ielts["questions"].append({
            "id": qid, "section": "listening", "type": "lst_sc",
            "topic": q["topic"], "audio_text": q["audio_text"],
            "text_parts": q["text_parts"], "answer": q["answer"],
            "explanation": "Type each missing word/phrase exactly as you hear it. Spelling matters. Word limits apply (usually 1-3 words per blank).",
        })
        added_ielts += 1

    # Add listening tips to both
    for t in ("pte", "ielts"):
        raw["tests"][t].setdefault("tips", {})
        for key, tips in LISTENING_TIPS.items():
            raw["tests"][t]["tips"][key] = tips

    BANK.write_text(json.dumps(raw, indent=2, ensure_ascii=False))
    return added_pte, added_ielts


if __name__ == "__main__":
    p, i = build()
    print(f"Added {p} PTE Listening, {i} IELTS Listening.")
    bank = json.loads(BANK.read_text())
    print(f"Totals: PTE {len(bank['tests']['pte']['questions'])}, IELTS {len(bank['tests']['ielts']['questions'])}")
