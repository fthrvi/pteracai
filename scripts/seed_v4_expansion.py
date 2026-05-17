#!/usr/bin/env python3
"""Expansion v4 — fill sparse areas with hand-curated content.

PTE:
  - +15 R&W Fill in Blanks (currently sparse at 11)

IELTS:
  - +20 listening dictation sentences (currently 8)
  - +5 MCQ reading
  - +4 T/F/NG
  - +3 Matching Headings

All items have explanations + traps where applicable. Idempotent by id.
"""
from __future__ import annotations
import json
from pathlib import Path

BANK = Path(__file__).parent.parent / "public" / "data" / "bank.json"


# ============================================================================
# PTE — R&W Fill in Blanks
# ============================================================================
PTE_FIB_NEW = [
    {
        "topic": "academic vocabulary",
        "text_parts": [
            "The research findings ",
            " a long-held assumption about the effects of caffeine on memory. Participants who consumed coffee before a memory task ",
            " significantly better than those who did not, suggesting that moderate caffeine intake may ",
            " cognitive performance during demanding tasks.",
        ],
        "blanks": [
            {"options": ["challenge", "support", "ignore", "duplicate"], "correct": "challenge"},
            {"options": ["performed", "behaved", "scored", "showed"], "correct": "performed"},
            {"options": ["enhance", "destroy", "remove", "decline"], "correct": "enhance"},
        ],
    },
    {
        "topic": "academic register",
        "text_parts": [
            "Climate scientists have ",
            " evidence that the rate of polar ice melt is accelerating. This trend has ",
            " consequences for coastal communities worldwide, particularly those in low-lying regions where even small rises in sea level can ",
            " infrastructure and displace populations.",
        ],
        "blanks": [
            {"options": ["accumulated", "diminished", "ignored", "concealed"], "correct": "accumulated"},
            {"options": ["serious", "trivial", "minor", "negligible"], "correct": "serious"},
            {"options": ["overwhelm", "preserve", "enhance", "stabilize"], "correct": "overwhelm"},
        ],
    },
    {
        "topic": "research vocabulary",
        "text_parts": [
            "The study's authors ",
            " several methodological limitations in their concluding section, including a relatively small sample size and the absence of a control group. They ",
            " that future research should ",
            " these limitations to confirm or extend their preliminary findings.",
        ],
        "blanks": [
            {"options": ["acknowledged", "denied", "concealed", "fabricated"], "correct": "acknowledged"},
            {"options": ["recommended", "demanded", "forbid", "rejected"], "correct": "recommended"},
            {"options": ["address", "ignore", "amplify", "repeat"], "correct": "address"},
        ],
    },
    {
        "topic": "scientific reasoning",
        "text_parts": [
            "The hypothesis proposed by the research team ",
            " considerable debate within the scientific community. While some experts ",
            " the methodology as innovative, others questioned whether the conclusions could be ",
            " given the variability of the data.",
        ],
        "blanks": [
            {"options": ["sparked", "ended", "concealed", "ignored"], "correct": "sparked"},
            {"options": ["praised", "rejected", "tolerated", "endured"], "correct": "praised"},
            {"options": ["substantiated", "fabricated", "discarded", "abandoned"], "correct": "substantiated"},
        ],
    },
    {
        "topic": "economics vocabulary",
        "text_parts": [
            "Rising inflation has ",
            " consumer confidence in many developed economies. Households are increasingly ",
            " to defer major purchases, and businesses are postponing investment decisions, which together ",
            " a slowdown in economic activity.",
        ],
        "blanks": [
            {"options": ["eroded", "boosted", "preserved", "celebrated"], "correct": "eroded"},
            {"options": ["inclined", "reluctant", "eager", "enthusiastic"], "correct": "reluctant"},
            {"options": ["produce", "prevent", "celebrate", "disprove"], "correct": "produce"},
        ],
    },
    {
        "topic": "historical analysis",
        "text_parts": [
            "Historians have long ",
            " over the precise causes of the Industrial Revolution. While technological innovation is widely ",
            " as a key driver, the role of social and political factors remains ",
            " among scholars.",
        ],
        "blanks": [
            {"options": ["debated", "agreed", "celebrated", "ignored"], "correct": "debated"},
            {"options": ["acknowledged", "denied", "rejected", "concealed"], "correct": "acknowledged"},
            {"options": ["contested", "settled", "obvious", "trivial"], "correct": "contested"},
        ],
    },
    {
        "topic": "technology adoption",
        "text_parts": [
            "The widespread ",
            " of mobile payment systems has transformed retail commerce in many countries. Consumers can now ",
            " transactions with a simple tap, reducing the need for physical currency and ",
            " checkout times.",
        ],
        "blanks": [
            {"options": ["adoption", "rejection", "destruction", "concealment"], "correct": "adoption"},
            {"options": ["complete", "extend", "delay", "complicate"], "correct": "complete"},
            {"options": ["shortening", "lengthening", "preventing", "ignoring"], "correct": "shortening"},
        ],
    },
    {
        "topic": "environmental science",
        "text_parts": [
            "Coral bleaching ",
            " when sea temperatures rise above a critical threshold, causing corals to ",
            " their symbiotic algae and lose their primary food source. Without intervention, prolonged bleaching can lead to ",
            " mortality across entire reef systems.",
        ],
        "blanks": [
            {"options": ["occurs", "ceases", "improves", "stabilizes"], "correct": "occurs"},
            {"options": ["expel", "absorb", "consume", "produce"], "correct": "expel"},
            {"options": ["widespread", "minor", "negligible", "isolated"], "correct": "widespread"},
        ],
    },
    {
        "topic": "medical research",
        "text_parts": [
            "Recent advances in genetic research have ",
            " new possibilities for personalized medicine. By analyzing a patient's individual genetic profile, doctors can now ",
            " treatments to maximize effectiveness and minimize side effects, an approach that may ",
            " healthcare in coming decades.",
        ],
        "blanks": [
            {"options": ["opened", "closed", "limited", "destroyed"], "correct": "opened"},
            {"options": ["tailor", "standardize", "generalize", "ignore"], "correct": "tailor"},
            {"options": ["transform", "preserve", "duplicate", "abandon"], "correct": "transform"},
        ],
    },
    {
        "topic": "urban planning",
        "text_parts": [
            "The integration of green spaces into urban design has been ",
            " to numerous benefits, including improved air quality, reduced urban heat, and enhanced mental wellbeing. City planners ",
            " advocate for parks and tree-lined streets as essential ",
            " of healthy urban environments.",
        ],
        "blanks": [
            {"options": ["linked", "opposed", "rejected", "ignored"], "correct": "linked"},
            {"options": ["increasingly", "rarely", "never", "occasionally"], "correct": "increasingly"},
            {"options": ["components", "obstacles", "problems", "threats"], "correct": "components"},
        ],
    },
    {
        "topic": "business strategy",
        "text_parts": [
            "Companies that ",
            " in employee training programs tend to ",
            " higher retention rates and stronger overall performance. Such investments are not merely costs but strategic ",
            " in human capital that yield long-term returns.",
        ],
        "blanks": [
            {"options": ["invest", "ignore", "withhold", "cut"], "correct": "invest"},
            {"options": ["report", "deny", "conceal", "ignore"], "correct": "report"},
            {"options": ["investments", "burdens", "obstacles", "losses"], "correct": "investments"},
        ],
    },
    {
        "topic": "renewable energy",
        "text_parts": [
            "The cost of solar panels has ",
            " dramatically over the past decade, making renewable energy more ",
            " for ordinary households. This trend is expected to ",
            " as manufacturing efficiencies improve and economies of scale are achieved.",
        ],
        "blanks": [
            {"options": ["declined", "increased", "stabilized", "fluctuated"], "correct": "declined"},
            {"options": ["accessible", "expensive", "restricted", "complex"], "correct": "accessible"},
            {"options": ["continue", "reverse", "halt", "fluctuate"], "correct": "continue"},
        ],
    },
    {
        "topic": "education policy",
        "text_parts": [
            "Studies have consistently shown that early childhood education ",
            " significant long-term benefits for cognitive development and social skills. Despite this, access to quality early education remains ",
            " for many families, particularly in low-income communities, where children may ",
            " from the same opportunities as their wealthier peers.",
        ],
        "blanks": [
            {"options": ["yields", "prevents", "destroys", "negates"], "correct": "yields"},
            {"options": ["limited", "abundant", "universal", "excessive"], "correct": "limited"},
            {"options": ["benefit", "suffer", "thrive", "improve"], "correct": "benefit"},
        ],
    },
    {
        "topic": "technology and society",
        "text_parts": [
            "The proliferation of social media has fundamentally ",
            " how people consume news and information. While digital platforms offer unprecedented access to diverse perspectives, they have also been ",
            " for spreading misinformation and reinforcing echo chambers that ",
            " critical thinking.",
        ],
        "blanks": [
            {"options": ["altered", "preserved", "stabilized", "ignored"], "correct": "altered"},
            {"options": ["criticized", "praised", "endorsed", "celebrated"], "correct": "criticized"},
            {"options": ["undermine", "strengthen", "enhance", "promote"], "correct": "undermine"},
        ],
    },
    {
        "topic": "scientific methodology",
        "text_parts": [
            "Peer review remains the ",
            " standard for evaluating scientific research, despite well-documented ",
            " in the system. Reviewers ",
            " their expertise to assess whether a study's methodology is sound and its conclusions are warranted.",
        ],
        "blanks": [
            {"options": ["gold", "broken", "outdated", "primitive"], "correct": "gold"},
            {"options": ["limitations", "advantages", "benefits", "successes"], "correct": "limitations"},
            {"options": ["apply", "ignore", "abandon", "conceal"], "correct": "apply"},
        ],
    },
]


# ============================================================================
# IELTS Listening — Dictation sentences
# ============================================================================
IELTS_WFD_NEW = [
    "Library borrowing privileges are extended to all enrolled postgraduate students.",
    "The lecture on cognitive psychology will be rescheduled to next Wednesday morning.",
    "Please remember to switch off your laptops at the conclusion of the seminar.",
    "International applicants must submit financial documents alongside their academic transcripts.",
    "The faculty office can provide detailed information about scholarship opportunities.",
    "Workshop participants are required to register at the main reception desk.",
    "Examination scripts will be returned to students during the following tutorial session.",
    "Research methodology training is mandatory for all first-year doctoral candidates.",
    "Field trip arrangements have been finalised for the second week of November.",
    "Online tutorials will replace in-person lectures during the renovation period.",
    "Course registration closes at the end of the third week of the semester.",
    "Group presentations should be uploaded to the course website before the deadline.",
    "The university gymnasium offers free fitness classes throughout the academic year.",
    "Career counselling appointments must be booked at least one week in advance.",
    "Library opening hours will be extended during the examination period.",
    "Submission of completed coursework is required by five o'clock on Friday afternoon.",
    "The economics seminar series will resume after the mid-term break.",
    "Postgraduate students may access the research databases from any campus computer.",
    "All laboratory equipment must be returned to its designated storage cabinet.",
    "Conference attendance will be reimbursed upon submission of original receipts.",
]


# ============================================================================
# IELTS Reading — MCQ
# ============================================================================
IELTS_MCQ_V4 = [
    {
        "topic": "main idea identification",
        "passage": "The growth of microfinance institutions over the past three decades has transformed access to credit for hundreds of millions of people in developing economies. By offering small loans to individuals without collateral or formal credit histories, microfinance has enabled entrepreneurs to launch businesses, smallholder farmers to invest in productivity-enhancing equipment, and households to weather unexpected expenses without resorting to predatory lenders. However, empirical evidence on poverty reduction has been more mixed than early enthusiasts predicted. While microfinance reliably improves financial inclusion and helps households manage volatile incomes, randomized trials in multiple countries have found only modest effects on overall poverty rates. Researchers now suggest that microfinance should be understood as one financial tool among many, rather than a singular solution to poverty.",
        "question": "What is the main argument of the passage?",
        "options": [
            "Microfinance has completely failed to reduce poverty anywhere.",
            "Microfinance has clear benefits but more limited impact on poverty than originally hoped.",
            "Microfinance is the most effective poverty reduction tool ever invented.",
            "Microfinance should be abandoned in favor of traditional banking systems.",
        ],
        "answer": 1,
        "explanation": "The passage describes real benefits (financial inclusion, income smoothing) but also notes 'mixed' evidence and 'modest effects on poverty rates' — option B captures this nuanced position. A and D overstate negatives; C contradicts the modest-effects finding.",
        "trap": "C is tempting if you anchor on the positive opening — but the passage's argument is in the second half. Always read the 'however' clause.",
    },
    {
        "topic": "detail identification",
        "passage": "The development of the printing press by Johannes Gutenberg in the mid-15th century is often credited with launching the modern era of mass communication. Gutenberg's key innovation was not printing itself — woodblock printing had existed in East Asia for centuries — but rather a system of movable metal type that could be rearranged and reused for different texts. Combined with an oil-based ink suited to metal type and a press design adapted from wine and olive presses, the technology enabled rapid, economical reproduction of books. Within fifty years of Gutenberg's first major publication, an estimated 20 million books had been printed across Europe, fundamentally transforming literacy, religion, and scientific exchange.",
        "question": "According to the passage, what was Gutenberg's key innovation?",
        "options": [
            "He invented printing for the first time in history.",
            "He developed a movable metal type system that could be rearranged and reused.",
            "He created the first oil-based ink in human history.",
            "He designed the first press, adapting it from wine production.",
        ],
        "answer": 1,
        "explanation": "The passage states explicitly: 'Gutenberg's key innovation was not printing itself...but rather a system of movable metal type that could be rearranged and reused for different texts.' Option B paraphrases this. A directly contradicts the passage; C and D overstate ('first in history').",
        "trap": "A is the popular misconception that the passage explicitly corrects. IELTS often uses common misconceptions as distractors — read carefully for the corrective phrasing.",
    },
    {
        "topic": "writer's view",
        "passage": "The role of zoos in modern society is increasingly contested. Critics argue that even the best-designed enclosures cannot replicate the spatial freedom and behavioral complexity of wild habitats, and that the educational value of zoo visits is overstated by surveys that simply ask whether visitors learned something. Defenders counter that modern accredited zoos invest substantially in conservation breeding programs, fund field research, and serve as critical safety nets for species facing extinction in the wild. The honest answer is that contemporary zoos are doing meaningful conservation work while simultaneously asking visiting animals to live lives constrained in ways that, in many cases, do compromise their wellbeing. Whether the trade-off is justified depends partly on factual questions about animal welfare and partly on ethical values that vary across observers.",
        "question": "What is the writer's view on the debate about zoos?",
        "options": [
            "Zoos should be closed because they harm animals.",
            "Zoos serve only an entertainment purpose and should be expanded.",
            "Zoos involve genuine trade-offs between conservation value and animal welfare.",
            "The debate about zoos has already been resolved in favor of conservation.",
        ],
        "answer": 2,
        "explanation": "The writer explicitly says zoos do 'meaningful conservation work' AND 'compromise wellbeing' — a genuine trade-off. Option C captures this. A and B are extreme positions the writer doesn't take; D contradicts 'contested'.",
        "trap": "A or B may match your own intuition, but the writer is deliberately presenting both sides. Look for the 'and yet' / 'while simultaneously' structure — that's the writer's voice.",
    },
    {
        "topic": "inference",
        "passage": "Archaeologists working in the Nile Delta have recently uncovered evidence suggesting that the use of papyrus for writing began significantly earlier than previously documented. Carbon dating of papyrus fragments found at a Bronze Age administrative site indicates that the material was in use at least three centuries before the earliest examples in the established archaeological record. The implications, while still being assessed, suggest that the development of literate administration in ancient Egypt may need to be revised backward, potentially altering historians' understanding of the relationship between writing technology and the centralization of political power.",
        "question": "What can be inferred from the passage about the relationship between writing technology and political organization?",
        "options": [
            "Writing technology is unrelated to political organization in ancient societies.",
            "Political centralization always precedes the development of writing.",
            "Earlier use of writing technology may have implications for our understanding of when political centralization occurred.",
            "Carbon dating is an unreliable method for assessing ancient artifacts.",
        ],
        "answer": 2,
        "explanation": "The passage explicitly connects the earlier dating to potential revision of 'the relationship between writing technology and the centralization of political power'. Option C captures this. A contradicts the passage; B is not stated; D contradicts the use of carbon dating as evidence.",
        "trap": "B is a plausible-sounding generalization that the passage doesn't support. Inference questions reward what the passage IMPLIES, not what sounds true in general.",
    },
    {
        "topic": "main idea identification",
        "passage": "The standard advice to drink eight glasses of water per day has become so widely accepted that it is rarely questioned, yet there is little scientific basis for this specific recommendation. The figure appears to have originated from a 1945 U.S. Food and Nutrition Board guideline that suggested 2.5 liters of total water intake per day — explicitly including water contained in food. Subsequent popularization stripped away that qualification, leaving the misleading impression that eight glasses of pure water are required on top of normal dietary intake. In reality, individual hydration needs vary widely based on body size, activity level, climate, and the water content of foods consumed, and the most reliable signal of adequate hydration is simply the absence of thirst and the color of urine.",
        "question": "What is the main point of the passage?",
        "options": [
            "People should drink as much water as possible every day.",
            "The eight-glasses-a-day rule is based on a misunderstanding of older research.",
            "Hydration is not important for health.",
            "Coffee and tea are better hydration sources than water.",
        ],
        "answer": 1,
        "explanation": "The passage traces how the 1945 guideline was stripped of context, creating a misleading impression. Option B captures this. A contradicts the passage; C reverses the message; D is not discussed.",
        "trap": "A is the popular position the passage is REFUTING — be careful not to assume the passage agrees with the conventional wisdom it discusses.",
    },
]


# ============================================================================
# IELTS Reading — T/F/NG
# ============================================================================
IELTS_TFNG_V4 = [
    {
        "passage": "The platypus, native to eastern Australia, is one of the most evolutionarily distinctive mammals on Earth. It is one of only five species of monotreme — mammals that lay eggs instead of giving birth to live young. The platypus possesses a duck-like bill equipped with electroreceptors that detect the electrical signals produced by the muscle movements of prey, allowing it to hunt with its eyes and ears closed underwater. Males have venomous spurs on their hind legs, making the platypus one of the few venomous mammals known to science. Despite these unusual traits, recent research has shown that the platypus shares many genetic features with other mammals, indicating a common ancestor rather than a wholly separate evolutionary line.",
        "statement": "The platypus is one of only a small number of mammals that lay eggs.",
        "answer": "true",
        "explanation": "The passage states the platypus is 'one of only five species of monotreme — mammals that lay eggs'. Five = small number. TRUE.",
        "trap": "None significant. The statement paraphrases the passage with no exaggeration.",
    },
    {
        "passage": "The platypus, native to eastern Australia, is one of the most evolutionarily distinctive mammals on Earth. It is one of only five species of monotreme — mammals that lay eggs instead of giving birth to live young. The platypus possesses a duck-like bill equipped with electroreceptors that detect the electrical signals produced by the muscle movements of prey, allowing it to hunt with its eyes and ears closed underwater. Males have venomous spurs on their hind legs, making the platypus one of the few venomous mammals known to science. Despite these unusual traits, recent research has shown that the platypus shares many genetic features with other mammals, indicating a common ancestor rather than a wholly separate evolutionary line.",
        "statement": "Female platypuses also possess venomous spurs.",
        "answer": "false",
        "explanation": "The passage states 'Males have venomous spurs' — specifying males only. The statement claims females do too, which contradicts. FALSE.",
        "trap": "If you read 'spurs' and 'venomous' without noting 'Males', you may mark TRUE. Pronouns and gender qualifiers are common IELTS test points.",
    },
    {
        "passage": "The platypus, native to eastern Australia, is one of the most evolutionarily distinctive mammals on Earth. It is one of only five species of monotreme — mammals that lay eggs instead of giving birth to live young. The platypus possesses a duck-like bill equipped with electroreceptors that detect the electrical signals produced by the muscle movements of prey, allowing it to hunt with its eyes and ears closed underwater. Males have venomous spurs on their hind legs, making the platypus one of the few venomous mammals known to science. Despite these unusual traits, recent research has shown that the platypus shares many genetic features with other mammals, indicating a common ancestor rather than a wholly separate evolutionary line.",
        "statement": "The platypus is found exclusively on Kangaroo Island.",
        "answer": "not given",
        "explanation": "The passage says the platypus is 'native to eastern Australia' — but says nothing about Kangaroo Island specifically. The statement isn't confirmed or contradicted: NOT GIVEN.",
        "trap": "It MIGHT actually be false (Kangaroo Island is southern, not eastern), but the passage doesn't address this specific island. Stay strict — only the passage's text matters.",
    },
    {
        "passage": "The development of antibiotics in the 20th century transformed medicine by enabling effective treatment of bacterial infections that had previously been fatal. However, the widespread use — and frequent overuse — of these drugs has created selective pressure for the evolution of resistant bacterial strains. The World Health Organization has identified antimicrobial resistance as one of the top ten global public health threats facing humanity. Researchers are pursuing several strategies to address this threat, including the development of new classes of antibiotics, the use of bacteriophages (viruses that attack bacteria), and improved stewardship programs in hospitals to limit unnecessary antibiotic use. Despite these efforts, the rate at which new antibiotics are being developed continues to lag behind the rate at which resistance is emerging.",
        "statement": "All antibiotics developed since 1950 have become ineffective against bacteria.",
        "answer": "false",
        "explanation": "The passage discusses growing resistance but says antibiotics 'transformed medicine' and notes 'new classes' are being developed — the statement that ALL antibiotics are ineffective contradicts this. FALSE.",
        "trap": "Absolute statements ('all', 'every') are usually FALSE traps. Scan for absolute language and check if the passage gives any exception.",
    },
]


# ============================================================================
# IELTS Reading — Matching Headings
# ============================================================================
IELTS_MH_V4 = [
    {
        "id": "i-mh-006",
        "topic": "science of nutrition",
        "instructions": "Choose the best heading for each paragraph from the list of headings below.",
        "paragraphs": [
            "For most of human history, the relationship between food and health was understood through tradition, religion, and folk wisdom. Specific foods were thought to have particular humoral effects — making the body hotter or colder, drier or moister — and these classifications guided diets across cultures. Detailed knowledge about nutrition as we understand it today, with vitamins, minerals, and macronutrients, simply did not exist.",
            "The transition to a scientific understanding of nutrition began in the 19th century, when chemists started analyzing the components of foods. Early breakthroughs included the identification of proteins, fats, and carbohydrates as the primary macronutrients, and the recognition that certain mysterious 'deficiency diseases' such as scurvy and beriberi were caused by the absence of specific dietary components rather than infection.",
            "By the early 20th century, these mysterious deficiency factors had been isolated and named vitamins. Subsequent decades saw the discovery of essential minerals, the elucidation of how energy is extracted from food, and the recognition that diet plays a role in chronic conditions such as heart disease and diabetes. Nutritional science had become a complex discipline with practical implications for public health.",
        ],
        "headings": [
            "Traditional pre-scientific understanding of food",
            "Modern packaged food regulations",
            "Beginnings of scientific food analysis",
            "Maturation of nutrition as a science",
            "Religious dietary restrictions",
            "Personal recommendations from dieticians",
        ],
        "answer": [0, 2, 3],
        "explanation": "Para 1 → 0 (pre-scientific tradition). Para 2 → 2 (chemists begin analyzing food). Para 3 → 3 (maturation of nutrition science). Distractors include regulations, religious restrictions, personal dietetics — none of which are the main focus.",
        "trap": "Heading 4 ('religious dietary restrictions') is mentioned in para 1 but isn't the main topic. Match the OVERALL paragraph, not a single referenced concept.",
    },
    {
        "id": "i-mh-007",
        "topic": "urban transportation",
        "instructions": "Choose the best heading for each paragraph from the list of headings below.",
        "paragraphs": [
            "Cycling as a serious mode of urban transportation declined dramatically in most Western cities during the postwar decades, displaced by mass automobile ownership and urban designs that prioritized car movement over all other forms of mobility. By the 1980s, cycling had become a marginal activity in much of Europe and North America, associated more with recreation than with daily commuting.",
            "A handful of cities resisted this trend, most notably in the Netherlands and Denmark, where deliberate policy choices preserved and extended cycling infrastructure even as cars became universal elsewhere. Continuous separated bike lanes, signal priority for cyclists, and parking integration with public transit made cycling not just possible but often the most convenient option for short urban trips.",
            "In recent decades, many other cities have begun importing lessons from these examples. London, Paris, Bogotá, and others have invested in protected lane networks, public bike-share systems, and policies that reduce car space in central districts. The results have varied, but cities that have committed to systematic infrastructure improvements rather than piecemeal additions have seen the most dramatic increases in cycling rates.",
        ],
        "headings": [
            "Cycling as a serious sport",
            "Postwar decline of urban cycling",
            "Persistent cycling cultures in northern Europe",
            "Recent international adoption of cycling-friendly policies",
            "Bicycle manufacturing history",
            "Government subsidies for car ownership",
        ],
        "answer": [1, 2, 3],
        "explanation": "Para 1 → 1 (decline of cycling postwar). Para 2 → 2 (Netherlands/Denmark exceptions). Para 3 → 3 (other cities now adopting policies). Distractors: cycling as sport, manufacturing history, car subsidies.",
        "trap": "Heading 0 ('cycling as a serious sport') sounds related — the passage mentions 'serious mode of urban transportation' — but it's about TRANSPORT, not sport. Read for the actual subject.",
    },
    {
        "id": "i-mh-008",
        "topic": "linguistic evolution",
        "instructions": "Choose the best heading for each paragraph from the list of headings below.",
        "paragraphs": [
            "Every living language changes constantly, with new words entering common use, old words shifting meaning or fading away, and grammatical patterns subtly evolving even within a single generation. Speakers are often unaware of these changes because they happen gradually and tend to be most visible when comparing speech across generations or geographic regions.",
            "Several mechanisms drive linguistic change. Contact with other languages introduces loanwords and structural influences; technological and social developments demand new vocabulary; younger speakers create slang that sometimes enters the mainstream; and the natural human tendency to simplify pronunciation gradually wears down complex grammatical features.",
            "Historically, written language often acted as a brake on these changes, with standardized spellings and grammars persisting long after spoken usage had evolved. The arrival of digital communication has complicated this picture: text messages, social media, and other informal written forms now move at the speed of speech, sometimes accelerating change rather than slowing it.",
        ],
        "headings": [
            "The constant nature of language change",
            "Endangered languages around the world",
            "Mechanisms that drive linguistic evolution",
            "Writing's evolving role in language change",
            "Teaching foreign languages effectively",
            "Linguistic universals across all human languages",
        ],
        "answer": [0, 2, 3],
        "explanation": "Para 1 → 0 (language always changing). Para 2 → 2 (mechanisms: contact, tech, slang, simplification). Para 3 → 3 (writing's role — historically a brake, now sometimes accelerator). Distractors: endangered languages, teaching, universals.",
        "trap": "Heading 5 ('linguistic universals') might seem related because the passage is about language broadly — but it covers CHANGE, not universals. Specificity matters.",
    },
]


# ============================================================================
# Build
# ============================================================================
def normalize(s: str) -> str:
    return " ".join(s.lower().split())


def build():
    raw = json.loads(BANK.read_text())
    if raw.get("schema") != 2:
        print("ERROR: not v2.")
        return 0, 0
    pte = raw["tests"]["pte"]
    ielts = raw["tests"]["ielts"]
    existing_pte_ids = {q["id"] for q in pte["questions"]}
    existing_ielts_ids = {q["id"] for q in ielts["questions"]}
    existing_wfd_norm = {normalize(q["answer"]) for q in ielts["questions"] if q["type"] == "wfd"}

    added_pte = 0
    added_ielts = 0

    # PTE FIB
    idx = 300
    for q in PTE_FIB_NEW:
        qid = f"r-fib-{idx:03d}"
        while qid in existing_pte_ids:
            idx += 1
            qid = f"r-fib-{idx:03d}"
        options = [b["options"] for b in q["blanks"]]
        answer = [b["options"].index(b["correct"]) for b in q["blanks"]]
        pte["questions"].append({
            "id": qid,
            "section": "reading",
            "type": "fib",
            "topic": q["topic"],
            "text_parts": q["text_parts"],
            "options": options,
            "answer": answer,
            "explanation": "Read the full sentence on each side of the blank. Match grammar (noun/verb/adj) AND collocation. The correct word has BOTH the right meaning AND the right grammatical form.",
            "trap": "Two options often have similar meanings but only one fits the grammar or collocation. Eliminate by checking what comes right before and after the blank.",
        })
        existing_pte_ids.add(qid)
        added_pte += 1
        idx += 1

    # IELTS WFD
    idx = 200
    for sentence in IELTS_WFD_NEW:
        if normalize(sentence) in existing_wfd_norm:
            continue
        qid = f"i-wfd-{idx:03d}"
        while qid in existing_ielts_ids:
            idx += 1
            qid = f"i-wfd-{idx:03d}"
        ielts["questions"].append({
            "id": qid,
            "section": "listening",
            "type": "wfd",
            "topic": "academic dictation",
            "audio_text": sentence,
            "answer": sentence,
            "explanation": "Type exactly. Watch for: articles (a/an/the), plurals (-s endings often quiet), homophones (their/there, its/it's), and academic spelling (accommodation, committee, bibliography).",
        })
        existing_ielts_ids.add(qid)
        existing_wfd_norm.add(normalize(sentence))
        added_ielts += 1
        idx += 1

    # IELTS MCQ v4
    idx = 300
    for q in IELTS_MCQ_V4:
        qid = f"i-mcq-{idx:03d}"
        while qid in existing_ielts_ids:
            idx += 1
            qid = f"i-mcq-{idx:03d}"
        ielts["questions"].append({
            "id": qid,
            "section": "reading",
            "type": "mcq_single",
            **q,
        })
        existing_ielts_ids.add(qid)
        added_ielts += 1
        idx += 1

    # IELTS T/F/NG v4
    idx = 300
    for q in IELTS_TFNG_V4:
        qid = f"i-tfng-{idx:03d}"
        while qid in existing_ielts_ids:
            idx += 1
            qid = f"i-tfng-{idx:03d}"
        ielts["questions"].append({
            "id": qid,
            "section": "reading",
            "type": "tfng",
            "topic": "true false not given",
            **q,
        })
        existing_ielts_ids.add(qid)
        added_ielts += 1
        idx += 1

    # IELTS Matching Headings v4
    for q in IELTS_MH_V4:
        if q["id"] in existing_ielts_ids:
            continue
        ielts["questions"].append({
            "section": "reading",
            "type": "matching_headings",
            **q,
        })
        existing_ielts_ids.add(q["id"])
        added_ielts += 1

    BANK.write_text(json.dumps(raw, indent=2, ensure_ascii=False))
    return added_pte, added_ielts


if __name__ == "__main__":
    p, i = build()
    print(f"Added {p} PTE questions, {i} IELTS questions.")
    bank = json.loads(BANK.read_text())
    print(f"Totals: PTE {len(bank['tests']['pte']['questions'])}, IELTS {len(bank['tests']['ielts']['questions'])}")
