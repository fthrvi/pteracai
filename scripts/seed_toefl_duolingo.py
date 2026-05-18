#!/usr/bin/env python3
"""Seed TOEFL iBT + Duolingo English Test content into bank.json.

Both tests added with ~15 questions each using existing renderers:
  - TOEFL: mcq_single (Reading), lst_mcq (Listening), essay (Writing),
    read_aloud + ielts_part1 (Speaking)
  - Duolingo: fib (Read & Complete), wfd (Listen & Type), essay (Write
    About Photo / Topic), read_aloud, retell_lecture

Test-unique renderers (Sentence Insertion, Read & Select word/non-word,
Integrated Writing read+listen+write) skipped for v1; can be added
later if needed.

Idempotent — running again merges without duplicates.
"""
from __future__ import annotations
import json
from pathlib import Path

BANK = Path(__file__).parent.parent / "public" / "data" / "bank.json"


# ============================================================================
# TOEFL iBT — tips
# ============================================================================
TOEFL_TIPS = {
    "exam": [
        {"cat": "Test Format", "tip": "TOEFL iBT has 4 sections in this order: Reading (~36 min, 20 Qs across 2 passages), Listening (~36 min, 28 Qs), Speaking (17 min, 4 tasks), Writing (~50 min, 2 tasks). Total ~2 hours."},
        {"cat": "Test Format", "tip": "All sections delivered on computer with built-in note-taking. You CAN take notes on scratch paper throughout — required for Listening + Integrated Speaking + Integrated Writing."},
        {"cat": "Scoring", "tip": "Each section 0-30 = total 0-120. Most universities want 90-100+ overall, 22-26+ per section. Top programs require 100+ with 23+ in each."},
        {"cat": "Scoring", "tip": "Speaking and Writing scored by AI (SpeechRater + e-rater) AND human raters. Speaking heavily weights delivery (fluency, pronunciation, pace) — not just content."},
        {"cat": "Tricks", "tip": "Reading section is NOT adaptive — finish all questions in a passage before moving on; no penalty for going back within a passage but no return after submission."},
        {"cat": "Tricks", "tip": "Listening: take SPATIAL notes (lecture topic at top, main points down left, examples on right). Reconstruction is the entire game in Integrated Writing later."},
        {"cat": "Tricks", "tip": "Speaking task 1 (Independent) is the only one without reading/listening input — practice it with a 4-sentence template so prep time goes to content, not structure."},
    ],
    "reading_mcq_single": [
        {"cat": "Strategy", "tip": "TOEFL Reading questions follow passage order — Q5 comes from later in the passage than Q3. Don't re-read the whole thing for each question."},
        {"cat": "Strategy", "tip": "Vocabulary questions: a word is highlighted in context. The answer is usually the most COMMON meaning — TOEFL rarely tests obscure senses."},
        {"cat": "Strategy", "tip": "'Negative Factual' questions ('Which is NOT mentioned?') — eliminate options that ARE mentioned, the remaining one is your answer."},
        {"cat": "Strategy", "tip": "'Inference' questions: the answer is implied, never directly stated. Beware options that paraphrase the passage too closely — those are too direct."},
        {"cat": "Time", "tip": "~1.5 min per question. 10 questions per passage in 18 minutes. Tight."},
        {"cat": "Traps", "tip": "Rhetorical Purpose questions: WHY did the author include this paragraph? Answer is about the AUTHOR'S CHOICE, not the topic itself."},
        {"cat": "Tricks", "tip": "Final 'Summary' question (4 points) — pick 3 of 6 options that capture the main ideas. Skip the 3 that are minor details or false."},
    ],
    "listening_lst_mcq": [
        {"cat": "Strategy", "tip": "TOEFL lectures are 4-6 minutes. Take notes on: main topic, key terms defined, examples, professor's tone (skeptical? supportive?), connections to other concepts."},
        {"cat": "Strategy", "tip": "Conversations are office hours / student services. Always identify: what the student wants, what the problem is, what the professor/staff recommends."},
        {"cat": "Strategy", "tip": "Function questions: 'Why does the professor say X?' — the answer is the COMMUNICATIVE function (emphasizing, contrasting, joking), not the literal content."},
        {"cat": "Tricks", "tip": "Replay questions play a sentence back to you, then ask a follow-up. Listen for TONE in the replay — confusion, doubt, emphasis."},
        {"cat": "Tricks", "tip": "You CAN'T go back. Each question appears one at a time after the audio. Trust your notes — second-guessing wastes time."},
    ],
    "writing_essay": [
        {"cat": "Strategy", "tip": "TOEFL 'Academic Discussion' task replaced the old Independent Essay (2023+). You read a professor's question + 2 student responses, then write your own 100-word reply."},
        {"cat": "Strategy", "tip": "Academic Discussion: agree/disagree/extend one of the student responses, OR offer a third angle. Cite a SPECIFIC example or experience to back your view."},
        {"cat": "Templates", "tip": "Opener: 'I agree with [Student A] that... However, I would add that...' OR 'While both students raise valid points, I think the more important consideration is...'"},
        {"cat": "Templates", "tip": "Develop with: 'For example, in [country / industry / personal experience]...' Then close with implication."},
        {"cat": "Time", "tip": "Academic Discussion = 10 minutes. Aim for 110-130 words. The minimum is 100 but quality > exact word count."},
        {"cat": "Scoring", "tip": "Scored 0-5 by both AI (e-rater) and human. Top score requires: relevant + well-elaborated contribution to discussion, varied syntax, accurate language."},
    ],
    "speaking_read_aloud": [
        {"cat": "Strategy", "tip": "TOEFL doesn't have 'Read Aloud' as a separate task, but Speaking task 2 (Integrated) reads passages aloud as part of its delivery — clear pronunciation here is graded."},
    ],
    "speaking_ielts_part1": [
        {"cat": "Strategy", "tip": "TOEFL Speaking Task 1 (Independent) = pick a preference + explain why. 15 seconds prep, 45 seconds speak."},
        {"cat": "Templates", "tip": "Structure: 'I would [choice] because [reason 1] and [reason 2]. For example, [specific instance]. So while [opposite] has its appeal, [choice] is the better option for me.'"},
        {"cat": "Tricks", "tip": "Don't waste prep deciding — pick the option you have MORE examples for, even if it's not your honest preference. Content density matters more than truth."},
        {"cat": "Scoring", "tip": "0-4 scale, equal weight: Delivery (pace, pronunciation, intonation), Language Use (grammar, vocab range), Topic Development (coherent, fully addresses the prompt)."},
    ],
}


TOEFL_QUESTIONS = [
    # ---------- Reading (5 MCQ) ----------
    {
        "id": "t-r-mcq-001",
        "section": "reading",
        "type": "mcq_single",
        "topic": "factual information",
        "passage": "Throughout the eighteenth century, European naturalists assumed that fossils were simply unusual stones, products of geological processes rather than remnants of once-living organisms. This view shifted in the late 1700s with the work of Georges Cuvier, who systematically compared fossil bones to modern animal skeletons and demonstrated that some fossils represented species that no longer existed. Cuvier's argument for extinction—a controversial idea at the time—provided the foundation for the modern science of paleontology. His method of comparative anatomy became standard practice and influenced biology more broadly throughout the nineteenth century.",
        "question": "According to the passage, what did European naturalists believe about fossils before Cuvier's work?",
        "options": [
            "They were remnants of once-living organisms.",
            "They were unusual stones produced by geological processes.",
            "They proved the existence of extinct species.",
            "They were the result of comparative anatomy studies.",
        ],
        "answer": 1,
        "explanation": "The passage states that 'European naturalists assumed that fossils were simply unusual stones, products of geological processes rather than remnants of once-living organisms.' That's option B verbatim. Option A is the OPPOSITE — what Cuvier later proved. C and D are anachronistic — those came from Cuvier's work, not before.",
        "trap": "Option A is the most tempting because we now know fossils ARE organic remains — so it feels right. But the question asks what they believed BEFORE Cuvier. TOEFL Reading constantly tests whether you stick to what the passage says vs what you know.",
    },
    {
        "id": "t-r-mcq-002",
        "section": "reading",
        "type": "mcq_single",
        "topic": "vocabulary in context",
        "passage": "Coral reefs are among the most biologically diverse ecosystems on Earth, hosting roughly a quarter of all marine species despite covering less than one percent of the ocean floor. However, in recent decades, rising sea temperatures have caused widespread coral bleaching, a stress response in which the symbiotic algae living within coral tissues are expelled. Without these algae, corals lose their primary food source and may die within weeks if conditions do not improve.",
        "question": "The word 'expelled' in the passage is closest in meaning to:",
        "options": [
            "absorbed",
            "ignored",
            "ejected",
            "weakened",
        ],
        "answer": 2,
        "explanation": "In context, 'algae living within coral tissues are EXPELLED' means they are forced out. 'Ejected' (option C) is the closest synonym. 'Absorbed' is the opposite. 'Ignored' doesn't fit a physical process. 'Weakened' describes a different relationship.",
        "trap": "TOEFL Vocabulary questions test the CONTEXTUAL meaning, not the most common dictionary one. 'Expelled' can also mean 'removed from school' — irrelevant here. Match to the passage's specific usage.",
    },
    {
        "id": "t-r-mcq-003",
        "section": "reading",
        "type": "mcq_single",
        "topic": "inference",
        "passage": "The rapid expansion of the global solar industry has dramatically reduced manufacturing costs over the past decade, with the price per watt of photovoltaic panels falling by more than 80 percent. Yet despite these gains, residential adoption in the United States remains uneven. Installation costs—primarily labor, permitting, and electrical work—now make up a larger share of total project cost than the panels themselves. Industry analysts suggest that streamlining local permitting requirements could do as much to accelerate adoption as further reductions in panel prices.",
        "question": "What can be inferred from the passage about residential solar adoption in the United States?",
        "options": [
            "It has matched the dramatic decline in panel prices.",
            "It is primarily limited by the cost of photovoltaic panels.",
            "It is shaped by factors beyond the cost of panels alone.",
            "It will accelerate automatically as panel prices continue to fall.",
        ],
        "answer": 2,
        "explanation": "The passage notes panel prices fell 80% but adoption is 'uneven' AND installation costs now exceed panel costs AND permitting reform could matter as much as further price cuts. The inference: adoption depends on more than panel prices. Option C captures this. A contradicts 'uneven'. B is what was true before the price drop, not now. D is the opposite of the passage's argument.",
        "trap": "Option D is the conventional wisdom — 'cheaper panels = more adoption.' But the passage explicitly REJECTS this oversimplification. Inference questions reward what the passage IMPLIES, not what sounds plausible.",
    },
    {
        "id": "t-r-mcq-004",
        "section": "reading",
        "type": "mcq_single",
        "topic": "negative factual",
        "passage": "Sleep researchers have identified several distinct stages of sleep, each associated with characteristic brain activity. Stage 1 is the brief transition from wakefulness to sleep, lasting only a few minutes. Stage 2 follows, accounting for roughly half of total sleep time and characterized by reduced muscle activity and slower brain waves. Stages 3 and 4, sometimes grouped as 'slow-wave sleep,' are the deepest sleep stages and are thought to be most important for physical recovery. REM sleep, in which dreaming is most vivid, alternates with these non-REM stages throughout the night.",
        "question": "According to the passage, which of the following is NOT a characteristic of Stage 2 sleep?",
        "options": [
            "It accounts for about half of total sleep time.",
            "It involves reduced muscle activity.",
            "It is characterized by slower brain waves.",
            "It is the deepest stage of sleep.",
        ],
        "answer": 3,
        "explanation": "The passage attributes 'deepest sleep stages' to Stages 3 and 4 (slow-wave sleep), NOT Stage 2. Options A, B, C are all directly stated about Stage 2. Option D is wrong — that belongs to Stages 3-4.",
        "trap": "Negative-fact questions reverse normal MCQ logic — you're looking for the OPPOSITE of supported claims. Read each option asking 'is this in the passage about Stage 2?' If yes → eliminate. The one left over is your answer.",
    },
    {
        "id": "t-r-mcq-005",
        "section": "reading",
        "type": "mcq_single",
        "topic": "rhetorical purpose",
        "passage": "Throughout the early twentieth century, women in many Western countries waged determined campaigns for the right to vote. Suffrage movements employed a range of tactics—peaceful petitions, mass demonstrations, hunger strikes, even property destruction. The British suffragettes, for example, smashed shop windows and chained themselves to public buildings, drawing both public outrage and unprecedented media attention. While the violent tactics divided supporters and alienated some potential allies, historians today recognize that the combination of moderate and radical approaches together produced political change neither could have achieved alone.",
        "question": "Why does the author mention the British suffragettes' window-smashing and chaining tactics?",
        "options": [
            "To criticize violent political activism.",
            "To show that radical tactics alienated the public.",
            "To illustrate the range of methods suffrage movements used.",
            "To argue that peaceful petitions were ineffective.",
        ],
        "answer": 2,
        "explanation": "The British example follows the sentence 'a range of tactics—peaceful petitions, mass demonstrations, hunger strikes, even property destruction.' It serves as a CONCRETE ILLUSTRATION of that range. Option C captures the rhetorical purpose. A and D project a stance the author doesn't take; B describes one consequence but not the author's PURPOSE for including the example.",
        "trap": "Rhetorical Purpose questions ask WHY the author included something — focus on the AUTHOR'S CHOICE, not the topic itself. The British example serves the broader point about variety of tactics.",
    },

    # ---------- Listening (3 MCQ) ----------
    {
        "id": "t-l-mcq-001",
        "section": "listening",
        "type": "lst_mcq",
        "topic": "lecture detail",
        "audio_text": "Today we're going to talk about a fascinating phenomenon called bioluminescence — the ability of some living organisms to produce light. We see this most dramatically in deep-ocean creatures, where roughly 75 percent of species are bioluminescent. The light is produced by a chemical reaction between a substance called luciferin and an enzyme called luciferase. Now, what's interesting is that this trait has evolved INDEPENDENTLY at least 40 different times across the tree of life — meaning each lineage developed it separately. That's a strong signal that the ability to produce light has powerful adaptive value. Common functions include luring prey, deterring predators, attracting mates, and even camouflage — some fish produce light from their bellies to match the dim glow of the surface above and stay invisible from below.",
        "question": "According to the lecturer, what does the independent evolution of bioluminescence 40+ times suggest?",
        "options": [
            "That bioluminescence is a recent evolutionary trait.",
            "That bioluminescence has strong adaptive value.",
            "That all bioluminescent species share a common ancestor.",
            "That bioluminescence is found only in deep-ocean species.",
        ],
        "answer": 1,
        "explanation": "The lecturer says 'evolved independently at least 40 different times' and immediately notes 'That's a strong signal that the ability to produce light has powerful adaptive value.' Option B paraphrases this. C is the OPPOSITE — independent evolution means no common ancestor for the trait. A and D contradict the lecture.",
        "trap": "Option C is the intuitive answer if you don't catch the word 'independently' — common ancestry is the default mental model for traits. But the lecturer is making the OPPOSITE point.",
    },
    {
        "id": "t-l-mcq-002",
        "section": "listening",
        "type": "lst_mcq",
        "topic": "office hours conversation",
        "audio_text": "Student: Professor Andrews, I'm having trouble with the third assignment, the one on supply chain modeling. I understood the lectures, but when I try to set up the equations myself I just hit a wall. Professor Andrews: That's actually really common at this point in the course. Have you tried working through the practice problems in chapter seven? Those build up gradually — they start with two-stage chains and work up to the multi-tier networks that the assignment uses. Student: I did some of them. Maybe I went too fast through the early ones. Professor Andrews: That's likely it. Go back to problems three through seven and don't move on until you can do each one without looking at the solution. Once that clicks, the assignment will feel much more approachable.",
        "question": "What does Professor Andrews suggest the student do?",
        "options": [
            "Skip ahead to multi-tier network problems.",
            "Submit the assignment without finishing.",
            "Work through the chapter 7 practice problems carefully, in order.",
            "Drop the assignment and focus on later coursework.",
        ],
        "answer": 2,
        "explanation": "The professor explicitly says 'Go back to problems three through seven and don't move on until you can do each one without looking at the solution.' Option C paraphrases this. A is the opposite — building up from simple problems. B and D contradict the helpful tone of the advice.",
        "trap": "Standard TOEFL conversation question — listen for the EXPLICIT advice ('Go back to...') not implied. The student's own confusion ('went too fast') is a distractor that hints at what to fix, not the answer to the question.",
    },
    {
        "id": "t-l-mcq-003",
        "section": "listening",
        "type": "lst_mcq",
        "topic": "lecture function",
        "audio_text": "Now, when we look at the population data from the Industrial Revolution, we see something REALLY striking. In Britain between 1750 and 1850, the population nearly doubled — but agricultural output didn't double. Wages didn't double. Living standards for most workers, by some measures, actually DECLINED for the first several decades. So you might think: this looks like a recipe for disaster, right? But here's the thing — this is exactly the period when Britain becomes the world's leading industrial economy. So the question I want you to consider is: how does an economy GROW so dramatically when the average person's wellbeing is, by many measures, stagnant or worse?",
        "question": "Why does the lecturer pose the question at the end about how the economy can grow when wellbeing stagnates?",
        "options": [
            "To suggest that the Industrial Revolution was a failure.",
            "To frame the puzzle that the rest of the lecture will address.",
            "To argue that economic statistics are unreliable.",
            "To prove that wages always rise with industrial growth.",
        ],
        "answer": 1,
        "explanation": "The lecturer presents a paradox (economy grows, workers don't benefit) and ends with a question for students to consider — classic 'set up the lecture's central problem' move. Option B captures this rhetorical function. A misreads the lecturer's stance (presenting a puzzle ≠ calling something a failure). C and D distort the lecture.",
        "trap": "Function questions ask what the lecturer is DOING with their words, not just what they're saying. Posing a question at the end almost always sets up the rest of the lecture.",
    },

    # ---------- Writing (3 Essay-style — Academic Discussion) ----------
    {
        "id": "t-w-essay-001",
        "section": "writing",
        "type": "essay",
        "topic": "academic discussion",
        "prompt": "Your professor is teaching a class on environmental policy. Write a post responding to the professor's question. In your response you should:\n• Express and support your opinion.\n• Make a contribution to the discussion in your own words.\n\nProfessor: When governments fund research, they typically focus on either basic science (research without immediate practical application) or applied science (research aimed at solving specific problems). Given limited budgets, which should governments prioritize? Why?\n\nClassmate Maria: I believe governments should focus on applied science because it produces immediate, measurable benefits for taxpayers — new medical treatments, better infrastructure, cleaner energy. Basic science, while interesting, has uncertain payoffs.\n\nClassmate Jin: I disagree. Basic science is the foundation that applied science is built on. Without basic research into electromagnetism, we wouldn't have wireless technology. Cutting basic science is short-sighted.\n\nWrite a response of at least 100 words.",
        "rubric": "100-130 words. Engage with the professor's question AND with the classmates' positions. Take a clear stance with a specific example. Show your own perspective, not just paraphrase.",
        "grading_notes": "TOEFL Academic Discussion scored 0-5. Top score requires: relevant + well-elaborated contribution, specific example, varied syntax, accurate grammar. Pure agreement with one classmate without adding new angle = mid-range score.",
    },
    {
        "id": "t-w-essay-002",
        "section": "writing",
        "type": "essay",
        "topic": "academic discussion",
        "prompt": "Professor: Many universities require students to complete community service as a graduation requirement. Some argue this builds civic responsibility; others say it dilutes academic focus. Should community service be required?\n\nClassmate A: Yes — service teaches skills classrooms can't, and graduates with community engagement become better citizens. The mandate matters because most students wouldn't volunteer otherwise.\n\nClassmate B: No — forcing service makes it feel like a chore, not genuine help. Optional service programs attract students who actually want to be there and produce better outcomes.\n\nWrite a response of at least 100 words.",
        "rubric": "100-130 words. Address both views. Pick a side with reasoning. Real-world example expected.",
        "grading_notes": "Same TOEFL Academic Discussion rubric. Look for: clear position, engagement with both classmates' points, original contribution beyond paraphrase.",
    },
    {
        "id": "t-w-essay-003",
        "section": "writing",
        "type": "essay",
        "topic": "academic discussion",
        "prompt": "Professor: With remote work now common in many industries, some companies are reducing or eliminating physical office spaces. Is this shift good or bad for workers and businesses long-term?\n\nClassmate Y: Mostly good — workers save commute time, can live affordably outside expensive cities, and have more autonomy. Businesses save real estate costs.\n\nClassmate Z: Mostly bad — junior employees lose mentorship from in-person observation, team cohesion weakens, and the boundary between work and home erodes, hurting mental health.\n\nWrite a response of at least 100 words.",
        "rubric": "100-130 words. Engage with the trade-offs both classmates raise. Concrete example or scenario expected.",
        "grading_notes": "Same rubric. The strongest responses acknowledge the trade-off explicitly rather than picking 'good' or 'bad' simplistically.",
    },

    # ---------- Speaking (2 read_aloud + 2 ielts_part1-style independent) ----------
    {
        "id": "t-s-ra-001",
        "section": "speaking",
        "type": "read_aloud",
        "topic": "academic prose",
        "passage": "Recent research in cognitive psychology suggests that the brain's capacity to form new memories declines not steadily with age, but in distinct phases. Periods of relative stability are punctuated by sudden, more rapid declines, particularly during major life transitions such as retirement.",
        "rubric": "Read the passage aloud naturally. ~25 seconds. Clear pronunciation, natural intonation matching punctuation.",
        "grading_notes": "TOEFL Speaking doesn't have a 'Read Aloud' task per se, but reading clarity matters in Integrated Speaking tasks 2-3 where you read a passage. Practice for prosody and pace.",
    },
    {
        "id": "t-s-ra-002",
        "section": "speaking",
        "type": "read_aloud",
        "topic": "academic prose",
        "passage": "The integration of artificial intelligence into healthcare diagnostics has accelerated rapidly in recent years. While AI systems can now identify certain conditions with accuracy rivaling that of trained specialists, questions remain about accountability when these systems err and about how clinicians should incorporate AI recommendations into their decisions.",
        "rubric": "Read the passage aloud naturally. ~30 seconds. Match intonation to commas and periods.",
        "grading_notes": "Practice clear delivery — TOEFL grades Speaking on delivery (pace, pronunciation, intonation) heavily.",
    },
    {
        "id": "t-s-ip1-001",
        "section": "speaking",
        "type": "ielts_part1",
        "topic": "personal preference",
        "question": "Some students prefer to study in a quiet environment such as a library. Others prefer to study in a more lively environment such as a café. Which do you prefer and why?",
        "rubric": "TOEFL Independent Speaking Task 1. 15 sec prep, 45 sec speak. Pick a preference + 2 specific reasons + brief example.",
        "grading_notes": "Scored 0-4 each on Delivery, Language Use, Topic Development. Use a template: 'I prefer X because of two reasons. First... For example... Second... So while Y has appeal, X works better for me.'",
    },
    {
        "id": "t-s-ip1-002",
        "section": "speaking",
        "type": "ielts_part1",
        "topic": "personal preference",
        "question": "Some people believe it is better to learn about history by reading books. Others believe it is better to learn by visiting historical sites. Which do you prefer and why?",
        "rubric": "15 sec prep, 45 sec speak. Two reasons + concrete example.",
        "grading_notes": "Same rubric. Practice picking the option you have more examples for, not necessarily your honest preference.",
    },
]


# ============================================================================
# Duolingo English Test — tips
# ============================================================================
DUOLINGO_TIPS = {
    "exam": [
        {"cat": "Test Format", "tip": "Duolingo English Test (DET) is ~60 minutes, fully online, with adaptive difficulty (questions get harder if you do well). One overall score 10-160."},
        {"cat": "Test Format", "tip": "Mixed item types appear in random order. No predictable section structure like TOEFL/IELTS. Be ready to switch between Read & Complete, Listen & Type, Read Aloud, Write About Photo, etc."},
        {"cat": "Scoring", "tip": "Subscores: Literacy (Reading+Writing), Comprehension (Reading+Listening), Conversation (Listening+Speaking), Production (Writing+Speaking). Most universities want 110-130+ overall."},
        {"cat": "Tricks", "tip": "Adaptive scoring means HARDER questions = MORE points, but wrong answers don't penalize as much as in fixed-length tests. Push your limits early to unlock harder items."},
        {"cat": "Tricks", "tip": "Speaking and writing tasks have generous time limits but you don't have to use all of it. End your response when you've made your point clearly — silence wastes nothing."},
        {"cat": "Test Day", "tip": "Live human reviews flag suspicious behavior (eyes off screen, mouth movements suggesting prompts). Stay calm and look at the screen — don't read aloud silently to yourself."},
    ],
    "reading_fib": [
        {"cat": "Strategy", "tip": "DET 'Read & Complete' shows a passage with random letters missing from half the words (you fill in the missing parts). Use surrounding context — verb tense, prepositions, articles give it away."},
        {"cat": "Strategy", "tip": "Common patterns: 'th_' = 'the/that/this/them/they', 's_' often = 'so/some/such', 'b_' often = 'be/by/but/because'. Spot the function word first."},
        {"cat": "Time", "tip": "3 minutes per passage. Don't get stuck on one blank — move on and come back."},
        {"cat": "Tricks", "tip": "Spelling counts. 'recieve' loses the point even though context is right. When in doubt, sound it out slowly."},
    ],
    "listening_wfd": [
        {"cat": "Strategy", "tip": "DET 'Listen & Type' plays a sentence once or twice. Type exactly what you hear. ~1 minute total per item."},
        {"cat": "Strategy", "tip": "DET test-makers use natural conversational English, not just formal academic. Listen for contractions ('I've', 'can't', 'won't') and informal phrasing."},
        {"cat": "Traps", "tip": "Common errors: missing articles (a/an/the), wrong verb tense (-ed dropped), homophones (their/there/they're)."},
    ],
    "writing_essay": [
        {"cat": "Strategy", "tip": "DET 'Write About the Photo' = describe an image in 1 minute. ~50-90 words. We don't have actual photos here — practice with text descriptions of imagined images."},
        {"cat": "Strategy", "tip": "DET 'Write About the Topic' = respond to a prompt in 5 minutes. ~150 words minimum for top scores. More structured than the photo task."},
        {"cat": "Templates", "tip": "Photo: 'This image shows [main subject] [setting]. The most striking feature is [detail]. [Brief observation about mood/context].'"},
        {"cat": "Templates", "tip": "Topic: opener with thesis → 1-2 reasons with examples → brief conclusion. Standard 4-paragraph for 150 words."},
    ],
    "speaking_read_aloud": [
        {"cat": "Strategy", "tip": "DET 'Read Aloud' shows you a sentence and asks you to read it. Don't restart if you stumble — keep flowing."},
        {"cat": "Strategy", "tip": "Pace matters. Too slow = fluency score drops. Too fast = pronunciation suffers. Aim for natural conversational rate."},
    ],
    "speaking_retell_lecture": [
        {"cat": "Strategy", "tip": "DET 'Speak About the Topic' = monologue prompt with 30 sec prep + 90 sec speak. Build a mini-essay verbally: thesis + reason + example + conclusion."},
        {"cat": "Strategy", "tip": "DET 'Listen and Speak' alternates listening and speaking turns — like a short conversation with a robot. Keep responses natural and concise."},
    ],
}


DUOLINGO_QUESTIONS = [
    # ---------- Read & Complete (5 — using fib pattern with single-blank options) ----------
    {
        "id": "d-r-fib-001",
        "section": "reading",
        "type": "fib",
        "topic": "academic vocabulary",
        "text_parts": [
            "The popularity of remote work has ",
            " significantly since 2020, changing how millions of people ",
            " their daily routines and ",
            " their work-life balance.",
        ],
        "blanks": [
            {"options": ["grown", "shrunk", "stagnated", "vanished"], "correct": "grown"},
            {"options": ["organize", "ignore", "abandon", "punish"], "correct": "organize"},
            {"options": ["manage", "destroy", "celebrate", "demand"], "correct": "manage"},
        ],
    },
    {
        "id": "d-r-fib-002",
        "section": "reading",
        "type": "fib",
        "topic": "academic vocabulary",
        "text_parts": [
            "Scientists studying climate change have ",
            " evidence that rising temperatures are ",
            " agricultural patterns across multiple continents, with ",
            " consequences for food security.",
        ],
        "blanks": [
            {"options": ["gathered", "ignored", "rejected", "fabricated"], "correct": "gathered"},
            {"options": ["disrupting", "improving", "stabilizing", "celebrating"], "correct": "disrupting"},
            {"options": ["serious", "trivial", "imaginary", "convenient"], "correct": "serious"},
        ],
    },
    {
        "id": "d-r-fib-003",
        "section": "reading",
        "type": "fib",
        "topic": "academic vocabulary",
        "text_parts": [
            "The artist's most recent exhibition ",
            " considerable attention from critics, who praised both her ",
            " of color and her ability to ",
            " complex emotions through simple compositions.",
        ],
        "blanks": [
            {"options": ["attracted", "rejected", "destroyed", "concealed"], "correct": "attracted"},
            {"options": ["mastery", "ignorance", "rejection", "fear"], "correct": "mastery"},
            {"options": ["convey", "hide", "destroy", "ignore"], "correct": "convey"},
        ],
    },
    {
        "id": "d-r-fib-004",
        "section": "reading",
        "type": "fib",
        "topic": "academic vocabulary",
        "text_parts": [
            "The medical research team ",
            " hypothesized that diet alone could ",
            " certain chronic conditions, but recent studies ",
            " a more complex relationship between nutrition and health.",
        ],
        "blanks": [
            {"options": ["originally", "never", "rarely", "incorrectly"], "correct": "originally"},
            {"options": ["prevent", "cause", "ignore", "worsen"], "correct": "prevent"},
            {"options": ["suggest", "deny", "disprove", "conceal"], "correct": "suggest"},
        ],
    },
    {
        "id": "d-r-fib-005",
        "section": "reading",
        "type": "fib",
        "topic": "academic vocabulary",
        "text_parts": [
            "Despite ",
            " challenges, the construction project was completed on time and within budget, a feat that ",
            " careful planning and ",
            " cooperation between contractors and the city.",
        ],
        "blanks": [
            {"options": ["substantial", "trivial", "imaginary", "fictitious"], "correct": "substantial"},
            {"options": ["required", "prevented", "ignored", "discouraged"], "correct": "required"},
            {"options": ["effective", "broken", "absent", "harmful"], "correct": "effective"},
        ],
    },

    # ---------- Listen & Type (3 WFD-style) ----------
    {
        "id": "d-l-wfd-001",
        "section": "listening",
        "type": "wfd",
        "topic": "everyday english",
        "audio_text": "The meeting has been rescheduled to next Thursday at three in the afternoon.",
        "answer": "The meeting has been rescheduled to next Thursday at three in the afternoon.",
        "explanation": "Watch for 'rescheduled' (spelling), 'next' (not 'last'), and the time format ('three in the afternoon'). DET tends to use spoken-language time expressions.",
    },
    {
        "id": "d-l-wfd-002",
        "section": "listening",
        "type": "wfd",
        "topic": "everyday english",
        "audio_text": "Please remember to bring your laptop and a notebook to tomorrow's workshop.",
        "answer": "Please remember to bring your laptop and a notebook to tomorrow's workshop.",
        "explanation": "Article matters: 'a notebook' (not 'notebook'). Possessive: 'tomorrow's' with apostrophe + s. 'Laptop' is one word.",
    },
    {
        "id": "d-l-wfd-003",
        "section": "listening",
        "type": "wfd",
        "topic": "everyday english",
        "audio_text": "I've been trying to learn Spanish for about six months and it's going really well.",
        "answer": "I've been trying to learn Spanish for about six months and it's going really well.",
        "explanation": "Contractions: 'I've' and 'it's' — DET expects you to type contractions when you hear them, not expand to 'I have' / 'it is'.",
    },

    # ---------- Write About Photo/Topic (3 — using essay) ----------
    {
        "id": "d-w-photo-001",
        "section": "writing",
        "type": "essay",
        "topic": "write about photo",
        "prompt": "Imagine a photo showing a busy urban farmer's market on a sunny weekend morning. Describe what you might see in the photo. Write 50-90 words in about 1 minute.",
        "rubric": "50-90 words. Description of imagined setting, people, atmosphere. Use present continuous + descriptive vocabulary.",
        "grading_notes": "DET Write About Photo scored on Literacy + Production subscores. Specificity beats vague generalities — 'a woman is buying tomatoes' > 'people are shopping'.",
    },
    {
        "id": "d-w-photo-002",
        "section": "writing",
        "type": "essay",
        "topic": "write about photo",
        "prompt": "Imagine a photo of a young child concentrating intensely on building a tall structure with wooden blocks. Describe the scene. Write 50-90 words in about 1 minute.",
        "rubric": "50-90 words. Focus on the child's expression, posture, surroundings.",
        "grading_notes": "DET rewards specific observations and varied sentence structure even in short responses.",
    },
    {
        "id": "d-w-topic-001",
        "section": "writing",
        "type": "essay",
        "topic": "write about topic",
        "prompt": "Some people believe that learning a second language is much easier when you live in a country where it's spoken. Others think you can learn equally well through online classes and self-study. What do you think? Why? Give specific examples in your response.\n\nWrite 150+ words in about 5 minutes.",
        "rubric": "150+ words. 4-paragraph structure: opener with thesis, 1-2 reasons with examples, brief conclusion.",
        "grading_notes": "DET Write About Topic scored on Literacy + Production. Top scores require: clear position, specific examples, varied vocabulary, controlled grammar.",
    },

    # ---------- Speak About Topic (2 — using retell_lecture) ----------
    {
        "id": "d-s-topic-001",
        "section": "speaking",
        "type": "retell_lecture",
        "topic": "speak about topic",
        "passage": "Topic prompt: Describe a skill you would like to learn in the future and explain why. You'll have 30 seconds to prepare and 90 seconds to speak.",
        "rubric": "Speak for 60-90 seconds after 30 sec prep. Build a mini-essay: introduce the skill, give 1-2 reasons you want it, end with what learning it would change.",
        "grading_notes": "DET Speak About Topic scored on Production + Conversation. Look for: clear structure, specific examples, fluent delivery, natural intonation.",
    },
    {
        "id": "d-s-topic-002",
        "section": "speaking",
        "type": "retell_lecture",
        "topic": "speak about topic",
        "passage": "Topic prompt: Describe a place that is important to you and explain why it matters. You'll have 30 seconds to prepare and 90 seconds to speak.",
        "rubric": "Speak for 60-90 seconds. Where + why + what makes it meaningful.",
        "grading_notes": "Same rubric. Practice ending strongly with a 'so to me, that place represents...' line.",
    },

    # ---------- Read Aloud (2) ----------
    {
        "id": "d-s-ra-001",
        "section": "speaking",
        "type": "read_aloud",
        "topic": "sentence",
        "passage": "Researchers have discovered that regular exercise can significantly reduce the risk of developing several chronic diseases.",
        "rubric": "Read the sentence aloud naturally. ~10 seconds. Clear pronunciation, natural intonation.",
        "grading_notes": "DET Read Aloud is short — 1-2 sentences. Quality over speed.",
    },
    {
        "id": "d-s-ra-002",
        "section": "speaking",
        "type": "read_aloud",
        "topic": "sentence",
        "passage": "The new library will open to the public next month after extensive renovations to improve accessibility and digital resources.",
        "rubric": "Read aloud naturally. Match intonation to the comma and end stress.",
        "grading_notes": "Practice pausing at commas, ending sentences with falling tone.",
    },
]


# ============================================================================
# Build
# ============================================================================
def build():
    raw = json.loads(BANK.read_text())
    if raw.get("schema") != 2:
        print("ERROR: bank is not v2.")
        return 0, 0

    # Add TOEFL bank
    if "toefl" not in raw["tests"]:
        raw["tests"]["toefl"] = {"label": "TOEFL iBT", "short": "TOEFL", "tips": {}, "questions": []}
    toefl = raw["tests"]["toefl"]
    toefl.setdefault("tips", {})
    toefl.setdefault("questions", [])
    existing_toefl = {q["id"] for q in toefl["questions"]}
    added_toefl = 0
    for q in TOEFL_QUESTIONS:
        if q["id"] in existing_toefl:
            continue
        toefl["questions"].append(q)
        added_toefl += 1
    toefl["tips"] = TOEFL_TIPS

    # Add Duolingo bank
    if "duolingo" not in raw["tests"]:
        raw["tests"]["duolingo"] = {"label": "Duolingo English Test", "short": "Duolingo", "tips": {}, "questions": []}
    duo = raw["tests"]["duolingo"]
    duo.setdefault("tips", {})
    duo.setdefault("questions", [])
    existing_duo = {q["id"] for q in duo["questions"]}
    added_duo = 0
    for q in DUOLINGO_QUESTIONS:
        if q["id"] in existing_duo:
            continue
        duo["questions"].append(q)
        added_duo += 1
    duo["tips"] = DUOLINGO_TIPS

    BANK.write_text(json.dumps(raw, indent=2, ensure_ascii=False))
    return added_toefl, added_duo


if __name__ == "__main__":
    t, d = build()
    print(f"Added {t} TOEFL questions, {d} Duolingo questions.")
    bank = json.loads(BANK.read_text())
    print(f"Bank totals:")
    for k, v in bank["tests"].items():
        print(f"  {k}: {len(v['questions'])} questions, {sum(len(x) for x in v.get('tips', {}).values())} tips")
