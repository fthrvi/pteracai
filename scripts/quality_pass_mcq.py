#!/usr/bin/env python3
"""Quality pass — hand-crafted explanations + traps for the 11 most-likely
PTE MCQ items (r-mcq-100 through r-mcq-110), replacing the template
explanations that were inserted during the goarno scrape.

Each item gets:
  - explanation: WHY the correct option is right, naming the distinction
    from the closest wrong option
  - trap: which specific distractor is the most-tempting wrong choice
    and the cognitive shortcut that makes it tempting

Idempotent — updates fields by id.
"""
from __future__ import annotations
import json
from pathlib import Path

BANK = Path(__file__).parent.parent / "public" / "data" / "bank.json"


UPDATES = {
    "r-mcq-100": {
        "explanation": "Option B captures the dual challenge the passage names: regulating tech so it 'benefits everyone' WITHOUT 'compromising privacy and freedom'. A removes the regulatory dimension. C reverses the ethical concern. D conflates the policymaker's role with accelerating adoption (not what the passage says). E is the opposite extreme — total prevention.",
        "trap": "A is the most tempting because the passage discusses 'harnessing potential' positively. But the actual MAIN CHALLENGE is the balance, not pure unrestricted harnessing. Always read for what the question specifically asks (challenge, not opportunity).",
    },
    "r-mcq-101": {
        "explanation": "Option B paraphrases the passage almost word-for-word: 'urgency of unity and innovative approaches to address environmental and health challenges'. A redirects to economic inequality (not in the passage). C narrows to pandemic-specific funding. D narrows to renewable energy. E narrows to bilateral diplomacy.",
        "trap": "C and D are tempting because they pick out single themes (health, environment) that ARE mentioned. But the keynote's PRIMARY focus is the broader call for unity and innovation — main idea questions reward the umbrella claim, not a specific sub-theme.",
    },
    "r-mcq-102": {
        "explanation": "Option C captures the three functions named in the passage: air quality, urban heat reduction, wildlife habitats — and explicitly links them to 'urban sustainability'. A reduces to property values (a side effect, not the main role). B mentions aesthetics + social, missing the environmental functions. D and E understate or contradict.",
        "trap": "B is the most tempting trap — aesthetics IS one of the roles named ('aesthetic enhancements') and the passage does mention people benefit. But the question asks about urban SUSTAINABILITY specifically, which is the environmental dimension. Match the question's exact word.",
    },
    "r-mcq-103": {
        "explanation": "Option B directly paraphrases the passage's opening prescription: 'understand your garden's environment' + 'how much sun and shade'. A skips the analysis step entirely. C is a generic suggestion not specified. D and E focus on soil quality, which isn't the FIRST step the passage names.",
        "trap": "D is the most-tempting trap because soil quality IS important for gardening. But the question asks about the FIRST step — and the passage explicitly says start with sun/shade understanding, before any soil work.",
    },
    "r-mcq-104": {
        "explanation": "Option D paraphrases the passage's cultural-enrichment example (restaurants, festivals, cultural events). A, B, C all use absolute language ('reduces', 'all', 'completely') that overstates what migration does. E is plausible but not stated as a benefit.",
        "trap": "Watch for absolute-language distractors: A's 'reduces overall costs', B's 'all migrants automatically', C's 'completely eliminates'. The passage never makes absolute claims. The correct option is hedged and specific.",
    },
    "r-mcq-105": {
        "explanation": "Option D directly states the PRIMARY benefit identified by the studies: extended life expectancy via nutrients and antioxidants. A, B, C all describe OTHER (more specific) potential effects but none is the 'primary' benefit named in the passage.",
        "trap": "A (mental clarity) is the most likely guess because it's commonly associated with healthy diets in popular discourse. But the question asks about the PRIMARY benefit per the studies cited — which is life expectancy, not cognition.",
    },
    "r-mcq-106": {
        "explanation": "Option B captures the BOTH challenges the passage explicitly lists: 'internal political divides AND external pressures'. A and E pick a single cause (economic, climate) the passage doesn't emphasize. C is fabricated. D's 'sole challenge' contradicts the passage's pluralistic framing.",
        "trap": "D's 'sole challenge' is an obvious red flag — the passage clearly names MULTIPLE challenges. Whenever an option uses 'only', 'sole', or 'exclusively', test it against the passage's plurality.",
    },
    "r-mcq-107": {
        "explanation": "Option C directly paraphrases the passage's two-pronged strategy: 'investing in technology AND education'. A and B describe alternative policies not named. D and E describe responses the passage doesn't credit.",
        "trap": "A (reducing taxes) and B (tariffs) are common policy debates in the news, so they feel relevant. But the passage specifically names tech + education investment — read what's stated, not what's popular.",
    },
    "r-mcq-108": {
        "explanation": "Option A paraphrases the passage's specific finding: 'loneliness and anxiety, especially among young people'. B, C, D, E all reverse the passage's negative framing into positives (better health, better relationships, better information, no inequality) — none align with 'negative effect'.",
        "trap": "The trap here is failing to notice the question asks about a NEGATIVE effect. If you skim and just look for 'social media' content, options C and D look plausible (community, information). Always re-read the question's framing word.",
    },
    "r-mcq-109": {
        "explanation": "Option B captures BOTH advantages the passage names: higher efficiency (>30%) AND cost-effectiveness from abundant materials. A reverses the materials claim (rare vs abundant). C narrows wrongly to physical size. D understates the conversion advantage. E claims durability not mentioned.",
        "trap": "A is the strongest reversal trap because it sounds technical and serious — but it directly contradicts the passage's 'abundant materials' claim. When two options state opposites, check the passage's exact wording.",
    },
    "r-mcq-110": {
        "explanation": "Option C captures the passage's stated lesson: 'early detection and rapid response' to 'prevent widespread transmission'. A, B, D, E each pick a related-but-not-stated response (PPE, healthcare reform, mental health, travel bans). These all sound reasonable but aren't the CRITICAL lesson the passage identifies.",
        "trap": "A (PPE access) and E (travel bans) are intuitive pandemic-management ideas. But the question asks what the passage names as critical — and the passage specifically names detection + response speed, not material/policy responses.",
    },
}


def build():
    raw = json.loads(BANK.read_text())
    pte = raw["tests"]["pte"]
    updated = 0
    for q in pte["questions"]:
        if q["id"] in UPDATES:
            q["explanation"] = UPDATES[q["id"]]["explanation"]
            q["trap"] = UPDATES[q["id"]]["trap"]
            updated += 1
    BANK.write_text(json.dumps(raw, indent=2, ensure_ascii=False))
    return updated


if __name__ == "__main__":
    n = build()
    print(f"Updated {n} PTE MCQ explanations + traps.")
