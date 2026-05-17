#!/usr/bin/env python3
"""Speaking section seed.

Adds the `speaking` section to both PTE and IELTS, with:

PTE:
  - read_aloud: 8 passages to read aloud (30-40s prep, then speak)
  - repeat_sentence: 10 sentences for hear-and-repeat
  - describe_image: 6 text-prompt visual descriptions (no images yet)
  - retell_lecture: 4 mini-lecture passages to listen and re-tell
  - answer_short: 8 short factual questions (1-3 word answers)

IELTS:
  - ielts_part1: 8 familiar-topic Q&A (hobbies, work, hometown)
  - ielts_part2: 6 cue cards (1-min prep, 2-min monologue)
  - ielts_part3: 6 follow-up discussion questions

Idempotent by id.
"""
from __future__ import annotations
import json
from pathlib import Path

BANK = Path(__file__).parent.parent / "public" / "data" / "bank.json"


# ============================================================================
# PTE Speaking
# ============================================================================
PTE_READ_ALOUD = [
    {
        "topic": "academic prose",
        "passage": "The transition from agriculture-based economies to industrial economies in the nineteenth century fundamentally altered patterns of human settlement. Cities expanded rapidly as workers moved from rural areas to be near factories, leading to unprecedented growth in urban populations and the development of new social institutions to manage this concentration of people.",
    },
    {
        "topic": "academic prose",
        "passage": "Scientific discoveries often emerge from unexpected sources. The development of penicillin, for instance, began with Alexander Fleming's chance observation in 1928 that a mold contaminating his bacterial cultures had killed the bacteria around it. This serendipitous finding ultimately revolutionized medicine and saved countless lives.",
    },
    {
        "topic": "academic prose",
        "passage": "Renewable energy sources, including solar, wind, and hydroelectric power, have become increasingly cost-competitive with traditional fossil fuels over the past decade. Government incentives, technological improvements, and growing economies of scale have all contributed to this trend, transforming the global energy landscape in ways few anticipated.",
    },
    {
        "topic": "academic prose",
        "passage": "The human brain contains approximately eighty-six billion neurons, each connected to thousands of others through specialized junctions called synapses. This vast network gives rise to consciousness, memory, and the full range of human behavior, though much about how these emergent properties arise from neural activity remains poorly understood.",
    },
    {
        "topic": "academic prose",
        "passage": "Climate change is reshaping ecosystems worldwide at a pace that exceeds the adaptive capacity of many species. Migration patterns are shifting, blooming and breeding seasons are changing, and the geographic ranges of many plants and animals are expanding toward the poles or higher elevations as average temperatures rise.",
    },
    {
        "topic": "academic prose",
        "passage": "The invention of writing, which occurred independently in several ancient civilizations, marked a fundamental shift in human cognition and culture. Writing allowed knowledge to accumulate across generations without the limitations of memory, enabled the rise of bureaucratic states, and ultimately made possible the systematic accumulation of scientific knowledge.",
    },
    {
        "topic": "academic prose",
        "passage": "Sleep researchers have identified two primary types of sleep: rapid eye movement sleep, during which most vivid dreaming occurs, and non-rapid eye movement sleep, which itself contains multiple distinct stages. These types alternate throughout the night in cycles of approximately ninety minutes, serving different functions for physical recovery and memory consolidation.",
    },
    {
        "topic": "academic prose",
        "passage": "The discovery of DNA's double helix structure by Watson and Crick in 1953 transformed biology by revealing how genetic information is encoded, replicated, and transmitted across generations. This breakthrough laid the foundation for modern molecular biology, genetic engineering, and our growing understanding of human disease.",
    },
]


PTE_REPEAT_SENTENCE = [
    "The professor's lecture on quantum mechanics was unexpectedly accessible to first-year students.",
    "Most undergraduate programs require students to complete a substantial research project before graduation.",
    "The library will remain closed throughout the winter break for essential maintenance work.",
    "Climate scientists agree that global temperatures will continue to rise without intervention.",
    "Successful entrepreneurs often credit their teams more than their own individual contributions.",
    "Modern medicine has dramatically extended life expectancy in most parts of the world.",
    "The university recently received a substantial grant to expand its research facilities.",
    "Students should consult their academic advisor before changing their declared major.",
    "Research suggests that regular exercise can significantly improve cognitive performance.",
    "Public transportation systems require sustained investment to remain efficient and reliable.",
]


PTE_DESCRIBE_IMAGE = [
    {
        "topic": "line graph",
        "prompt": "Imagine a line graph showing the percentage of households with broadband internet access in five different countries between 2000 and 2024. Describe what such a graph would likely show, including the overall trend, the most striking comparison between countries, and one specific data point you might highlight.",
    },
    {
        "topic": "bar chart",
        "prompt": "Imagine a bar chart comparing average monthly rainfall across four major cities in Asia. Describe what such a chart would show: the wettest city, the driest city, the seasonal pattern most prominent, and any unexpected feature worth noting.",
    },
    {
        "topic": "process diagram",
        "prompt": "Imagine a process diagram showing how recycled paper is produced from used newspapers. Describe the main stages: collection, pulping, removal of contaminants, formation of new paper sheets, and drying. Use sequence words like 'first', 'then', 'next', and 'finally'.",
    },
    {
        "topic": "pie chart",
        "prompt": "Imagine a pie chart showing how a typical adult spends their day, divided into work, sleep, leisure, eating, and other activities. Describe the largest slice, the smallest, and any unexpected proportions.",
    },
    {
        "topic": "map",
        "prompt": "Imagine a map comparing a city's layout in 1950 and 2024. Describe how the urban area has expanded, what new transport infrastructure has appeared, and what landmarks have changed or remained.",
    },
    {
        "topic": "comparative chart",
        "prompt": "Imagine a chart comparing renewable energy use by country: solar, wind, hydro, and biomass. Describe which country leads in each category, the overall ranking, and the most significant pattern you observe.",
    },
]


PTE_RETELL_LECTURE = [
    {
        "topic": "history of medicine",
        "passage": "Today I want to talk about the history of vaccination. The first widely-used vaccine was developed by Edward Jenner in 1796, when he observed that milkmaids who had caught a mild disease called cowpox seemed immune to the deadly smallpox. He took material from a cowpox sore and inoculated a young boy, who then proved resistant to smallpox exposure. While Jenner's method would not pass modern ethical review, it laid the foundation for immunology as a science. Today, vaccines work through several mechanisms: some use weakened viruses, some use only fragments of viral proteins, and the most recent generation uses messenger RNA to instruct cells to produce a target protein. Vaccination has been one of the most successful public health interventions in history, having eliminated smallpox entirely and brought several other diseases close to eradication.",
    },
    {
        "topic": "environmental science",
        "passage": "I'm going to discuss the concept of carbon sinks today. A carbon sink is any natural reservoir that absorbs more carbon dioxide than it releases. The world's two largest carbon sinks are the oceans, which absorb about a quarter of all human-produced CO2 each year, and forests, particularly tropical rainforests. When trees photosynthesize, they pull carbon out of the atmosphere and store it in their wood, leaves, and roots. This is why deforestation is a double threat to climate stability: not only does it release stored carbon when trees are burned or decompose, but it also removes the future absorption capacity those trees would have provided. Protecting and restoring forests is therefore one of the most cost-effective strategies in the global response to climate change.",
    },
    {
        "topic": "psychology",
        "passage": "In this lecture we'll examine cognitive dissonance, a concept introduced by Leon Festinger in the 1950s. Cognitive dissonance occurs when a person holds two conflicting beliefs simultaneously, or when their behavior contradicts a stated belief. The mental discomfort this creates motivates people to reduce the dissonance, usually by changing one of the conflicting beliefs rather than changing their behavior. This explains many puzzling human behaviors: why people who make difficult choices become more certain that they chose correctly after the fact, why members of cults become more committed when prophecies fail, and why people often justify minor unethical actions rather than acknowledge them. Understanding cognitive dissonance helps explain why simply presenting people with contradictory evidence rarely changes their minds, especially on emotionally invested topics.",
    },
    {
        "topic": "economics",
        "passage": "Today's lecture covers the concept of opportunity cost, which is fundamental to economic thinking. The opportunity cost of any choice is the value of the next best alternative you give up. For example, if you choose to spend an hour studying economics instead of working at a paying job, the opportunity cost is the wages you would have earned in that hour. Opportunity cost is often invisible because it's about what you don't see — the path not taken. But ignoring opportunity costs leads to bad decisions. Governments that invest heavily in one program forgo the benefits that other programs could have produced. Companies that pursue one product line cannot simultaneously pursue another. The discipline of asking 'what else could we be doing with these resources?' is at the heart of economic analysis.",
    },
]


PTE_ANSWER_SHORT = [
    {
        "topic": "everyday knowledge",
        "question": "What do you call the season between summer and winter?",
        "answer": "autumn or fall",
    },
    {
        "topic": "everyday knowledge",
        "question": "What is the opposite of 'expensive'?",
        "answer": "cheap or inexpensive",
    },
    {
        "topic": "academic knowledge",
        "question": "What instrument is used to measure temperature?",
        "answer": "thermometer",
    },
    {
        "topic": "everyday knowledge",
        "question": "What do you call a person who studies the stars and planets?",
        "answer": "astronomer",
    },
    {
        "topic": "academic knowledge",
        "question": "What is the largest organ in the human body?",
        "answer": "skin",
    },
    {
        "topic": "everyday knowledge",
        "question": "How many continents are there in the world?",
        "answer": "seven",
    },
    {
        "topic": "academic knowledge",
        "question": "What is the chemical symbol for gold?",
        "answer": "Au",
    },
    {
        "topic": "everyday knowledge",
        "question": "What do you call a doctor who specializes in treating children?",
        "answer": "pediatrician",
    },
]


# ============================================================================
# IELTS Speaking
# ============================================================================
IELTS_PART1 = [
    {"topic": "hometown", "question": "Tell me about your hometown. What is it like to live there?"},
    {"topic": "work or studies", "question": "What do you do for work or study? Tell me about your daily routine."},
    {"topic": "free time", "question": "What do you usually do in your free time? Why do you enjoy it?"},
    {"topic": "family", "question": "Can you describe your family? Are you close to them?"},
    {"topic": "weather", "question": "What kind of weather do you prefer? Why?"},
    {"topic": "travel", "question": "Do you enjoy traveling? Where have you been recently?"},
    {"topic": "food", "question": "What kind of food do you like to eat? Have your tastes changed over time?"},
    {"topic": "technology", "question": "How often do you use a smartphone in a typical day? What for?"},
]


IELTS_PART2 = [
    {
        "topic": "describe a person",
        "prompt": "Describe a person who has had an important influence on your life. You should say:\n• who this person is\n• how you know them\n• what they did or do that has influenced you\n• and explain why this person has been so important to you.\n\nYou have 1 minute to prepare. Speak for 1-2 minutes.",
    },
    {
        "topic": "describe an experience",
        "prompt": "Describe a time when you learned something new that was difficult. You should say:\n• what it was\n• why you wanted to learn it\n• how you learned it\n• and explain how you felt when you eventually mastered it.\n\nYou have 1 minute to prepare. Speak for 1-2 minutes.",
    },
    {
        "topic": "describe a place",
        "prompt": "Describe a place you have visited that is particularly memorable. You should say:\n• where it is\n• when you went there\n• who you went with\n• and explain why it was so memorable for you.\n\nYou have 1 minute to prepare. Speak for 1-2 minutes.",
    },
    {
        "topic": "describe an object",
        "prompt": "Describe an item that is important to you. You should say:\n• what it is\n• how long you have had it\n• where you got it\n• and explain why this item is important to you.\n\nYou have 1 minute to prepare. Speak for 1-2 minutes.",
    },
    {
        "topic": "describe an activity",
        "prompt": "Describe a hobby or activity that you started recently. You should say:\n• what the hobby or activity is\n• when you started doing it\n• how you got into it\n• and explain why you enjoy doing it.\n\nYou have 1 minute to prepare. Speak for 1-2 minutes.",
    },
    {
        "topic": "describe a future plan",
        "prompt": "Describe a goal or plan you have for the next few years. You should say:\n• what the goal is\n• when you decided on it\n• what steps you are taking to achieve it\n• and explain why this goal is important to you.\n\nYou have 1 minute to prepare. Speak for 1-2 minutes.",
    },
]


IELTS_PART3 = [
    {"topic": "education", "question": "How has education changed in your country over the past few decades? What do you think drives those changes?"},
    {"topic": "technology", "question": "What impact has smartphone technology had on the way younger and older generations communicate? Is this a good thing?"},
    {"topic": "work", "question": "Some people work the same job their entire careers, while others change frequently. What are the advantages and disadvantages of each approach?"},
    {"topic": "environment", "question": "Whose responsibility is it to protect the environment — individuals, businesses, or governments? Why?"},
    {"topic": "culture", "question": "How important is it to preserve traditional cultural practices in a rapidly changing world? Can you give an example?"},
    {"topic": "globalization", "question": "Do you think globalization has been more positive or negative for ordinary people in your country? Why?"},
]


# ============================================================================
# Speaking Tips (added to both tests' tips with same content for now)
# ============================================================================
SPEAKING_TIPS = {
    "speaking_read_aloud": [
        {"cat": "Strategy", "tip": "Read silently during the 30-40s prep, identifying any difficult words or names. Mark mental pauses at commas and periods."},
        {"cat": "Strategy", "tip": "Speak at a steady moderate pace. Too fast → mispronunciation. Too slow → fluency penalty. Aim for natural conversational speed."},
        {"cat": "Strategy", "tip": "Use natural intonation — pitch rises at the start of sentences, falls at full stops, lifts slightly on commas. Robotic monotone tanks your score."},
        {"cat": "Tricks", "tip": "If you mispronounce a word, KEEP GOING. Self-correction signals lack of fluency to the AI scorer. Continuous flawed speech scores higher than perfect speech with restarts."},
        {"cat": "Tricks", "tip": "Open your mouth wider than feels natural. Clearer enunciation helps both human and AI assessment."},
        {"cat": "Scoring", "tip": "Read Aloud scores READING and SPEAKING — high leverage. ~6-7 items per test. Focus practice here pays double."},
    ],
    "speaking_repeat_sentence": [
        {"cat": "Strategy", "tip": "Listen ACTIVELY without trying to write or memorize visually. Your auditory memory is better than your visual recall under time pressure."},
        {"cat": "Strategy", "tip": "Pay particular attention to the LAST 3 words. Memory's recency effect makes the end most recoverable when you start speaking."},
        {"cat": "Strategy", "tip": "Repeat with the same INTONATION you heard. Matching prosody (pitch + rhythm) signals to the AI that you grasped the sentence structure."},
        {"cat": "Tricks", "tip": "If you blank on the middle, mumble plausibly with confident intonation. Fluency score is partially independent of content score."},
        {"cat": "Tricks", "tip": "Start speaking IMMEDIATELY after the beep — even a half-second delay can ding your fluency rating."},
        {"cat": "Scoring", "tip": "Repeat Sentence dual-scores LISTENING + SPEAKING. ~10-12 items per test — the single most-tested speaking task."},
    ],
    "speaking_describe_image": [
        {"cat": "Strategy", "tip": "Use a 4-sentence template that fits ANY image: (1) 'This [chart/image] shows...' (2) main trend or striking feature (3) one specific detail or comparison (4) 'Overall, the image suggests...'"},
        {"cat": "Strategy", "tip": "25 seconds total. Don't try to describe everything — pick the headline + one supporting detail. Fluency > completeness."},
        {"cat": "Strategy", "tip": "Plan ONE strong opening sentence during the 25s prep window. The first 5 seconds of speech sets the AI's impression."},
        {"cat": "Tricks", "tip": "Substitute 'things' / 'elements' / 'aspects' when you can't recall a precise word. Continuous speech > word-perfect pause."},
        {"cat": "Tricks", "tip": "Memorize trend vocabulary: 'rose sharply', 'declined gradually', 'fluctuated', 'reached a peak', 'remained stable'. Drop one or two in every description."},
    ],
    "speaking_retell_lecture": [
        {"cat": "Strategy", "tip": "Take notes during the lecture using KEYWORDS only, not full sentences. You have very little writing time — capture nouns and verbs."},
        {"cat": "Strategy", "tip": "Use a skeleton template: 'The lecturer mainly discussed [topic]. He/She began by [point 1]. Then he/she explained [point 2]. Furthermore, [point 3]. To conclude, [overall takeaway].'"},
        {"cat": "Strategy", "tip": "Even partial recall scores well if you have the structure. Don't panic if you miss specific details — fluent reconstruction beats precise silence."},
        {"cat": "Tricks", "tip": "Group your notes spatially: topic at top, examples on the left, key claims on the right. Spatial structure helps reconstruction."},
        {"cat": "Scoring", "tip": "Re-tell Lecture dual-scores LISTENING + SPEAKING. Worth template-memorization investment."},
    ],
    "speaking_answer_short": [
        {"cat": "Strategy", "tip": "One-word or short-phrase answers. If asked 'What is the opposite of empty?', say 'full' and stop. Don't elaborate."},
        {"cat": "Strategy", "tip": "If you genuinely don't know, give a related word in the same domain. 'Don't know' or silence scores zero; a wrong-but-domain-relevant attempt may score partial."},
        {"cat": "Tricks", "tip": "Respond immediately. Hesitation often costs more than a wrong answer here — the task tests instant retrieval, not deliberation."},
    ],
    "speaking_ielts_part1": [
        {"cat": "Strategy", "tip": "Aim for 2-3 sentence answers — not a one-word reply, not a monologue. Show range and detail without overrunning."},
        {"cat": "Strategy", "tip": "Include a personal example or specific detail in each answer. 'I usually walk in the park' is fine; 'I usually walk in Hyde Park in the morning because it's quiet' is better."},
        {"cat": "Tricks", "tip": "Use the question's exact tense and verb form in your answer. If asked 'Do you enjoy...?', answer with 'I enjoy...' (not 'I am enjoying' or 'I have enjoyed')."},
        {"cat": "Tricks", "tip": "Sprinkle in 1-2 IELTS-target vocabulary items per answer (varied, interesting, beneficial, particularly). The examiner is noting your vocabulary range from the very first question."},
    ],
    "speaking_ielts_part2": [
        {"cat": "Strategy", "tip": "Use the full 1-minute prep. Write 4 keywords on the prompt card: one for each bullet point. Don't try to write sentences."},
        {"cat": "Strategy", "tip": "Aim for 2 minutes of speech. Don't let the examiner stop you early — fill the time with examples, descriptions, and personal feelings."},
        {"cat": "Strategy", "tip": "Structure: intro sentence → address each bullet in order → personal feeling or conclusion. Treat the bullet list as a guarantee that ALL of them will be assessed."},
        {"cat": "Templates", "tip": "Opener: 'I'd like to talk about [X]. This is something/someone particularly meaningful to me because...'"},
        {"cat": "Templates", "tip": "Linking phrases: 'What makes this special is...' / 'I particularly remember...' / 'Looking back on it now...' — these elevate your discourse markers score."},
        {"cat": "Tricks", "tip": "Speak slowly enough to think ahead by ~3 seconds. You'll never run out of things to say if you're always one step ahead."},
    ],
    "speaking_ielts_part3": [
        {"cat": "Strategy", "tip": "These are abstract/analytical questions. Show range by giving a position, an example, AND acknowledging an opposing view ('Some people would argue, however, that...')."},
        {"cat": "Strategy", "tip": "Aim for 3-4 sentence answers. More than Part 1, less than Part 2. The examiner can interject and move on if you're concise."},
        {"cat": "Tricks", "tip": "Use 'I think', 'I believe', 'In my opinion' SPARINGLY — once max per answer. Replace with 'It seems to me', 'Arguably', 'One could argue' for vocabulary range."},
        {"cat": "Tricks", "tip": "When asked 'Why?' or 'How?', give a CAUSE-AND-EFFECT explanation, not just a list. 'Because X, this leads to Y, which means Z.' Coherence/cohesion is scored."},
    ],
    "speaking_general": [
        {"cat": "Setup", "tip": "Speaking tasks here use your browser's microphone and the Web Speech API for transcription (Chrome works best, Safari OK, Firefox limited). LLM grades the transcript content — the live exam additionally scores pronunciation and fluency."},
        {"cat": "Setup", "tip": "Allow microphone permission when prompted. PteracAI doesn't store audio — only the transcript is sent for grading."},
        {"cat": "Caveat", "tip": "What's NOT scored here: pronunciation accuracy, oral fluency, prosody. These require specialized audio analysis. For full-fidelity practice, supplement with mock tests that include pronunciation scoring."},
        {"cat": "Caveat", "tip": "Web Speech API recognition quality varies by browser, accent, and connection. If transcription seems off, try Chrome on desktop for best accuracy."},
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

    # PTE Speaking
    for i, q in enumerate(PTE_READ_ALOUD):
        qid = f"s-ra-{100+i:03d}"
        if qid in existing_pte_ids: continue
        pte["questions"].append({
            "id": qid, "section": "speaking", "type": "read_aloud",
            "topic": q["topic"], "passage": q["passage"],
            "rubric": "Read the passage aloud. Aim for natural pace, clear pronunciation, and matching intonation to punctuation. Don't restart if you mispronounce.",
            "grading_notes": "PTE Read Aloud is dual-scored on READING and SPEAKING. The 4 components in scoring are: content (did you read all words), oral fluency, pronunciation, and prosody. Transcript-based grading here covers content only.",
        })
        added_pte += 1
    for i, sentence in enumerate(PTE_REPEAT_SENTENCE):
        qid = f"s-rs-{100+i:03d}"
        if qid in existing_pte_ids: continue
        pte["questions"].append({
            "id": qid, "section": "speaking", "type": "repeat_sentence",
            "topic": "academic sentence",
            "audio_text": sentence, "expected": sentence,
            "rubric": "Listen to the sentence and repeat it exactly. Match the rhythm and intonation, not just the words.",
            "grading_notes": "Dual-scored on LISTENING and SPEAKING. Components: content (% of words matched), oral fluency, pronunciation. Transcript matching here scores content; live exam adds fluency and pronunciation.",
        })
        added_pte += 1
    for i, q in enumerate(PTE_DESCRIBE_IMAGE):
        qid = f"s-di-{100+i:03d}"
        if qid in existing_pte_ids: continue
        pte["questions"].append({
            "id": qid, "section": "speaking", "type": "describe_image",
            "topic": q["topic"], "prompt": q["prompt"],
            "rubric": "Speak for 25 seconds. Use a 4-sentence template: introduction, main feature, specific detail, overall conclusion. Don't pause to find words.",
            "grading_notes": "Scored on content (covered the key features?), oral fluency, and pronunciation. We use text prompts here in lieu of actual images; describe what the image would likely show.",
        })
        added_pte += 1
    for i, q in enumerate(PTE_RETELL_LECTURE):
        qid = f"s-rl-{100+i:03d}"
        if qid in existing_pte_ids: continue
        pte["questions"].append({
            "id": qid, "section": "speaking", "type": "retell_lecture",
            "topic": q["topic"], "passage": q["passage"],
            "rubric": "Listen to the lecture (or read it), then re-tell it in 40 seconds. Use a template: 'The lecturer discussed... He/She explained... Furthermore... To conclude...'",
            "grading_notes": "Dual-scored on LISTENING and SPEAKING. Scoring: content, fluency, pronunciation. Partial recall with strong structure scores better than full recall with hesitation.",
        })
        added_pte += 1
    for i, q in enumerate(PTE_ANSWER_SHORT):
        qid = f"s-as-{100+i:03d}"
        if qid in existing_pte_ids: continue
        pte["questions"].append({
            "id": qid, "section": "speaking", "type": "answer_short",
            "topic": q["topic"], "question": q["question"], "answer": q["answer"],
            "rubric": "One word or short phrase. Don't elaborate.",
            "grading_notes": "Scored on whether your answer matches an acceptable response. Quick response time matters — hesitation hurts almost as much as wrong content.",
        })
        added_pte += 1

    # IELTS Speaking
    for i, q in enumerate(IELTS_PART1):
        qid = f"i-sp1-{100+i:03d}"
        if qid in existing_ielts_ids: continue
        ielts["questions"].append({
            "id": qid, "section": "speaking", "type": "ielts_part1",
            "topic": q["topic"], "question": q["question"],
            "rubric": "Aim for 2-3 sentence answers with a personal example or specific detail. Match the question's tense and verb form.",
            "grading_notes": "IELTS Speaking Part 1 scores Fluency/Coherence, Lexical Resource, Grammar Range, Pronunciation. Each 25%. Content-based scoring here covers vocabulary range and grammar.",
        })
        added_ielts += 1
    for i, q in enumerate(IELTS_PART2):
        qid = f"i-sp2-{100+i:03d}"
        if qid in existing_ielts_ids: continue
        ielts["questions"].append({
            "id": qid, "section": "speaking", "type": "ielts_part2",
            "topic": q["topic"], "prompt": q["prompt"],
            "rubric": "Speak for 1-2 minutes after a 1-minute prep. Address all bullet points. Don't let yourself trail off early — fill the time.",
            "grading_notes": "IELTS Part 2 is the longest single speaking task. Scored on the same 4 criteria. Length, coverage of bullets, range of vocabulary, complex sentence structures, and natural fluency all matter.",
        })
        added_ielts += 1
    for i, q in enumerate(IELTS_PART3):
        qid = f"i-sp3-{100+i:03d}"
        if qid in existing_ielts_ids: continue
        ielts["questions"].append({
            "id": qid, "section": "speaking", "type": "ielts_part3",
            "topic": q["topic"], "question": q["question"],
            "rubric": "3-4 sentence answers. Take a position, give an example, acknowledge a contrary view. Use cause-and-effect when asked 'why'.",
            "grading_notes": "IELTS Part 3 tests abstract thinking. Scoring rewards opinion + example + nuance. Hedged claims (it seems, arguably, one could argue) score better than blunt assertions.",
        })
        added_ielts += 1

    # Speaking tips — add to both tests
    for t in ("pte", "ielts"):
        raw["tests"][t].setdefault("tips", {})
        for key, tips in SPEAKING_TIPS.items():
            raw["tests"][t]["tips"][key] = tips

    BANK.write_text(json.dumps(raw, indent=2, ensure_ascii=False))
    return added_pte, added_ielts


if __name__ == "__main__":
    p, i = build()
    print(f"Added {p} PTE Speaking, {i} IELTS Speaking.")
    bank = json.loads(BANK.read_text())
    print(f"Totals: PTE {len(bank['tests']['pte']['questions'])}, IELTS {len(bank['tests']['ielts']['questions'])}")
