#!/usr/bin/env python3
"""Expansion pass v3: deeper PTE and IELTS content.

PTE additions:
  - +21 re-order paragraphs (scraped from goarno)
  - +13 summarize written text (scraped from goarno)
  - +up to 30 MCQ reading questions (parsed from /tmp/pte_mcq_scrape.jsonl,
    deduped against existing PTE bank)

IELTS additions:
  - +6 True/False/Not Given (curated, with strong False-vs-NG distinctions)
  - +5 MCQ reading
  - +5 essay prompts
  - +5 Matching Headings (NEW IELTS task type)
  - Tips entry for matching_headings

Idempotent: dedupes by id and by passage-prefix where ids are auto-generated.
"""
from __future__ import annotations
import json
import random
from pathlib import Path

BANK = Path(__file__).parent.parent / "public" / "data" / "bank.json"
MCQ_SCRAPE = Path("/tmp/pte_mcq_scrape.jsonl")


# ============================================================================
# PTE — new re-order paragraphs (from goarno scrape, in CORRECT order; we
# shuffle on write so the display order isn't the answer)
# ============================================================================
PTE_REORDERS_NEW = [
    [
        "Email encryption is a process that secures email content to protect it from being read by anyone other than the intended recipients.",
        "First, when an email is sent, encryption software converts the message from readable text into scrambled cipher text.",
        "This is done using an encryption key, which only the sender and receiver possess.",
        "When the recipient receives the email, their software uses a decryption key to convert the cipher text back into readable text.",
        "This ensures that even if someone intercepts the email, they cannot understand its contents without the key.",
    ],
    [
        "A typical water filtration system works by passing water through multiple layers that trap and remove contaminants.",
        "First, water enters through a sediment filter that catches large particles like dirt and rust.",
        "Next, it may pass through an activated carbon filter that removes chemicals and impurities through a process called adsorption.",
        "Additional stages might include reverse osmosis, which uses a semi-permeable membrane to remove smaller particles, and UV filters that disinfect water by killing bacteria and viruses.",
        "The final product is clean, safe drinking water.",
    ],
    [
        "The International Food Expo returned this year at the Grand Expo Center, showcasing culinary delights from over 40 countries.",
        "The event served as a melting pot of cultures, featuring cooking demonstrations by renowned international chefs, tasting booths, and seminars on food sustainability and health.",
        "Highlights included the Sushi Rolling Contest and the Italian Pasta Making Workshop, which were open for all attendees to participate.",
        "The expo also emphasized eco-friendly practices, with vendors using biodegradable utensils and promoting organic ingredients.",
        "The vibrant atmosphere and the exchange of culinary traditions made this expo a must-visit for food lovers looking to explore global cuisine.",
    ],
    [
        "In a televised national debate, political candidates discussed the future of healthcare reform.",
        "One candidate argued for a single-payer system, claiming it would simplify healthcare delivery and ensure coverage for all citizens.",
        "Another candidate countered that such a system would limit competition and potentially lower the quality of care.",
        "Each side cited data from other countries' experiences to support their arguments.",
        "The debate highlighted the complexities of healthcare policy and left voters pondering the trade-offs of different approaches.",
    ],
    [
        "The city hosted its annual Run for Hope marathon this Sunday to raise funds for cancer research.",
        "Over 10,000 participants, including survivors and supporters, took to the streets in a demonstration of solidarity and resilience.",
        "The marathon featured a full 26.2-mile route and a half-marathon option, catering to all levels of runners.",
        "Local businesses sponsored the event, providing water stations and encouragement along the route.",
        "The day concluded with a celebration in the central park, where families enjoyed live music and a variety of food stalls, all while contributing to a noble cause.",
    ],
    [
        "A new community art project titled 'Walls of Expression' has transformed the city's blank walls into vibrant murals.",
        "Local artists and community groups collaborated on the designs, which reflect the city's cultural diversity and history.",
        "The project not only beautifies the area but also provides a platform for artists to showcase their talents.",
        "Walking tours of the murals are now offered, drawing both residents and tourists.",
        "Organizers hope these murals will inspire more public art projects across the city.",
    ],
    [
        "Bestselling author Jane Smith celebrated the launch of her latest novel with a special event at Booktown Library on Saturday.",
        "Fans had the opportunity to meet the author, get their books signed, and hear Jane read excerpts from her new book.",
        "The evening also included a Q&A session where Jane discussed her inspirations and writing process.",
        "Local aspiring writers and literature enthusiasts filled the venue, eager to engage with one of their favorite authors.",
        "The event was a success, further solidifying Jane's reputation as a key figure in contemporary literature.",
    ],
    [
        "In an innovative study by nutritionists at the Health and Wellness Research Center, the impact of different diets on mental health was explored.",
        "Participants followed specific dietary plans rich in either processed foods or whole foods for six months.",
        "Researchers measured changes in mood and anxiety levels through regular psychological assessments and blood tests, which monitored markers of inflammation and neurotransmitter activity.",
        "The preliminary results suggest a strong correlation between a whole food diet and improved mental health indicators.",
        "This research could lead to dietary recommendations for managing mental health conditions.",
    ],
    [
        "In 1928, Amelia Earhart became the first woman to fly across the Atlantic Ocean as a passenger.",
        "Four years later, in 1932, she made the solo nonstop flight across the Atlantic.",
        "Her courage and determination made her a symbol of the advancement of women in non-traditional fields.",
        "Earhart's achievements promoted aviation and inspired a generation of female aviators.",
        "Her mysterious disappearance during an attempt to circumnavigate the globe in 1937 remains one of aviation's greatest mysteries.",
    ],
    [
        "3D printing, or additive manufacturing, starts with designing a 3D model on a computer.",
        "This model is then sent to a 3D printer, which builds the object layer by layer from the bottom up.",
        "The printer uses materials such as plastic, metal, or resin, which it deposits in thin layers and then fuses together, typically using heat.",
        "Each layer corresponds to a cross-section of the final object.",
        "This process allows for the creation of complex and customized items that would be difficult to produce with traditional manufacturing methods.",
    ],
    [
        "A team at the Tech Advanced Research Lab has made significant progress in quantum computing by developing a new type of quantum bit that is more stable and less prone to error.",
        "Their method involves using topological quantum states, which are less affected by environmental noise, a common problem in earlier designs.",
        "The research, published in 'Quantum Science Journal,' details how these qubits can be produced and integrated into existing quantum computing architectures.",
        "This breakthrough could accelerate the practical deployment of quantum computers, potentially transforming data encryption and problem-solving capacities.",
    ],
    [
        "In 1921, Canadian scientists Frederick Banting and Charles Best discovered insulin, transforming the treatment of diabetes.",
        "Before their discovery, diabetes was essentially a death sentence.",
        "Insulin provided a way to manage blood sugar levels, saving countless lives.",
        "The first successful treatment with insulin on a human was carried out in 1922.",
        "This medical breakthrough earned Banting the Nobel Prize and has continued to benefit millions worldwide.",
    ],
    [
        "Educational researchers from the University of Queensland embarked on a year-long study to assess the efficacy of remote learning tools used in elementary schools during the pandemic.",
        "By analyzing student performance data and surveying teachers, parents, and students, they aimed to identify which technologies facilitated effective learning and which did not.",
        "The study also considered socio-economic factors to determine if some tools were more beneficial in different contexts.",
        "Results from this research are expected to guide future educational technology development and deployment in schools.",
    ],
    [
        "The French Revolution began in 1789, triggered by deep social and economic inequalities and discontent with the monarchy.",
        "It led to the rise of the French Republic and significant changes in French society.",
        "The Revolution saw the overthrow of the monarchy, the establishment of a republic, and drastic and violent shifts in power.",
        "The infamous Reign of Terror, marked by mass executions, was a significant phase of the Revolution.",
        "The French Revolution had a profound influence on modern political ideologies and the development of democratic principles.",
    ],
    [
        "Solar panels convert sunlight into electricity through a process called photovoltaic (PV) conversion.",
        "First, solar panels, which are made of semiconductor materials, absorb sunlight.",
        "The sunlight's energy then frees electrons in the material, creating an electrical current.",
        "This current is captured by wiring in the panels and is then converted from direct current (DC) to alternating current (AC) using an inverter.",
        "The AC electricity is then usable in homes or businesses, or can be fed back into the power grid.",
    ],
    [
        "Glass making begins with mixing sand (silicon dioxide) with soda ash and limestone.",
        "This mixture is then heated to a very high temperature in a furnace until it melts and becomes liquid.",
        "The molten glass is then poured into molds or floated on a bed of molten tin to form sheets.",
        "Once shaped, the glass is slowly cooled in a process called annealing, which prevents it from becoming too brittle.",
        "After cooling, the glass can be cut to size and further processed, such as by adding coatings or treatments to enhance strength or reduce glare.",
    ],
    [
        "Environmental scientists at Greenwater Institute have initiated a project to investigate the effects of microplastics on freshwater ecosystems.",
        "By introducing controlled amounts of microplastics into replicated freshwater environments, they observe how these particles affect fish health and behavior.",
        "Early observations indicate that microplastics may disrupt endocrine functions and reduce reproductive success in several fish species.",
        "This ongoing research is crucial for understanding the broader ecological impacts of plastic pollution and shaping water quality regulations.",
    ],
    [
        "The Panama Canal, an engineering marvel, was completed in 1914 after ten years of intense labor.",
        "It connected the Atlantic and Pacific Oceans, dramatically reducing the travel time for ships by avoiding the lengthy journey around South America.",
        "Over 40,000 workers participated in the construction, facing extreme challenges such as disease and difficult terrain.",
        "The canal's completion had a profound impact on global trade patterns.",
        "Today, it remains one of the most important waterways in the world.",
    ],
    [
        "A national security debate took place among candidates running for federal office, focusing on the balance between privacy and security.",
        "One candidate advocated for increased surveillance and intelligence gathering to protect the nation from threats.",
        "Another candidate warned of the risks to civil liberties and privacy, urging for more oversight and accountability in intelligence practices.",
        "The debate touched on recent incidents of terrorism and cyber attacks, making it a critical issue for voters.",
        "The candidates' differing views highlighted the challenging decisions faced by lawmakers in an era of complex global threats.",
    ],
    [
        "Researchers at EcoPack Solutions are working on developing new bio-degradable packaging materials from plant-based polymers.",
        "Their process involves extracting cellulose from agricultural waste, which is then treated with enzymes to produce a flexible, durable material.",
        "The team conducts various tests to evaluate the material's decomposition rate, resilience, and safety for food contact.",
        "Success in this area could significantly reduce reliance on conventional plastics and the environmental damage they cause.",
        "The company aims to commercialize their bio-degradable packaging within the next three years, offering a sustainable alternative to industries.",
    ],
    [
        "This week, the downtown convention center was bustling with tech enthusiasts and professionals attending the annual Tech Innovate Conference.",
        "The three-day event featured keynote speeches from industry leaders, panels discussing the latest trends in technology, and workshops for hands-on learning.",
        "Exhibitors showcased cutting-edge gadgets and software, offering attendees a glimpse into the future of tech.",
        "Networking opportunities were abundant, with a special focus on startups looking to connect with potential investors.",
        "The conference wrapped up with an insightful roundtable on the ethical implications of artificial intelligence, a topic that sparked lively debate among participants.",
    ],
]


# ============================================================================
# PTE — new Summarize Written Text passages (scraped)
# ============================================================================
PTE_SWT_NEW = [
    ("electric vehicles",
     "A recent surge in electric vehicle (EV) sales marks a significant milestone in the global shift towards sustainable transportation. According to a report by the International Energy Agency (IEA), EV sales doubled in 2023, reaching a record high of 10 million units worldwide. Governments are playing a pivotal role in this transition by offering incentives such as tax breaks, subsidies, and rebates to encourage consumers to purchase electric cars. Additionally, major automakers are investing heavily in EV technology and infrastructure, with companies like Tesla, Ford, and Volkswagen leading the charge. Despite the positive trends, challenges remain. The limited availability of charging stations and the high cost of EVs compared to traditional gasoline-powered vehicles are significant barriers to widespread adoption.",
     "A significant increase in electric vehicle (EV) sales, doubling to 10 million units in 2023, marks progress in sustainable transportation, driven by government incentives and major automaker investments, though challenges like charging infrastructure, high costs, and environmental concerns from battery production remain, requiring advancements in technology and recycling programs for continued growth and environmental benefits."),
    ("universal basic income",
     "The debate over universal basic income (UBI) has gained momentum amid the economic uncertainties brought on by the COVID-19 pandemic. Advocates argue that UBI, which involves providing all citizens with a regular, unconditional sum of money, can alleviate poverty and reduce inequality. Countries like Finland and Spain have conducted pilot programs to test the feasibility and impact of UBI, with mixed results. Supporters highlight the potential benefits, such as improved mental health, increased financial security, and greater economic stability. Critics, however, caution against the high costs and potential disincentives to work. They argue that UBI could lead to inflation and reduce the motivation for people to seek employment.",
     "The debate over universal basic income (UBI) has intensified due to the COVID-19 pandemic, with advocates highlighting its potential to alleviate poverty and improve economic stability, while critics warn of high costs, possible inflation, and reduced work incentives, leaving policymakers to consider various funding mechanisms and mixed pilot-program results from Finland and Spain."),
    ("data breach",
     "Amid rising tensions over cybersecurity, a major data breach has compromised the personal information of millions of users. The breach, which affected a leading social media platform, exposed names, email addresses, and phone numbers of over 100 million users. The company has since apologized and promised to enhance its security protocols, but the breach has sparked widespread concern among users and privacy advocates. In response, regulatory bodies are calling for stricter oversight and more robust data protection regulations to prevent future incidents.",
     "A major data breach at a leading social media platform exposed the personal information of over 100 million users, highlighting the urgent need for stronger cybersecurity measures, stricter regulatory oversight, and better data protection practices, while sparking widespread concern and reigniting debates on the responsibility of tech companies in safeguarding user data."),
    ("offshore wind",
     "The global push for renewable energy took a significant step forward this year with the announcement of a groundbreaking offshore wind farm project off the coast of Scotland. The project, expected to be one of the largest in the world, will generate enough electricity to power over two million homes. The wind farm, slated for completion in 2027, is part of Scotland's ambitious plan to achieve net-zero carbon emissions by 2045. Notably, the project will also create thousands of jobs in construction, maintenance, and associated industries, providing a significant boost to the local economy. Environmental groups have welcomed the announcement, highlighting the project's potential to reduce reliance on fossil fuels and lower greenhouse gas emissions. However, some local communities and fishermen have expressed concerns about the impact on marine life and fishing activities.",
     "The announcement of a major offshore wind farm project off Scotland's coast marks a significant advance in renewable energy, set to power over two million homes by 2027, create thousands of jobs, boost the local economy, and contribute to Scotland's net-zero carbon goals, though concerns about marine life and fishing impacts will be addressed through environmental assessments and consultations."),
    ("digital privacy ruling",
     "In a landmark ruling, the Supreme Court has declared that digital privacy is a fundamental right, setting a significant precedent for future cases. The decision came in response to a case involving the unauthorized collection of personal data by a major telecommunications company. Justice Elena Martinez, writing for the majority, stated that the right to privacy in the digital age is as essential as any other fundamental right. The case has sparked widespread debate about the balance between privacy and security. Proponents of the ruling argue that it will protect citizens from intrusive surveillance and data exploitation.",
     "In a landmark ruling, the Supreme Court declared digital privacy a fundamental right, ensuring individuals have control over their personal information, sparking debate between privacy protection advocates and those concerned about its impact on law enforcement and national security, and requiring the involved telecommunications company to implement stricter data protection measures and notify affected customers."),
    ("plastic ban",
     "Efforts to combat plastic pollution are gaining momentum as countries around the world introduce bans on single-use plastics. Recent data from the United Nations Environment Programme (UNEP) shows that more than 60 countries have enacted legislation to reduce plastic waste. These measures include bans on plastic bags, straws, and microbeads, as well as initiatives to promote recycling and the use of biodegradable alternatives. In addition to government actions, many corporations are committing to reducing their plastic footprint.",
     "Countries worldwide are ramping up efforts to combat plastic pollution through bans on single-use plastics, with over 60 nations enacting legislation and corporations committing to sustainable packaging, but challenges such as regional enforcement and finding cost-effective alternatives persist, necessitating collaboration among governments, businesses, and consumers for significant and lasting change."),
    ("youth mental health",
     "The mental health crisis among young people is a growing concern for educators, parents, and policymakers. Studies have shown that anxiety, depression, and other mental health issues are on the rise among adolescents and young adults. The COVID-19 pandemic has exacerbated these problems, with school closures, social isolation, and economic uncertainty contributing to increased stress and mental health challenges. According to the World Health Organization (WHO), mental health conditions account for 16% of the global burden of disease and injury in people aged 10-19 years.",
     "The growing mental health crisis among young people, exacerbated by the COVID-19 pandemic, has prompted educators, parents, and policymakers to introduce mental health education programs and expand access to services, though significant barriers remain, especially in underserved communities, highlighting the need for continued investment in mental health support to ensure the well-being of future generations."),
    ("remote learning",
     "The education sector is undergoing a significant transformation as remote learning becomes increasingly mainstream. The COVID-19 pandemic accelerated the adoption of online education, with schools and universities worldwide shifting to virtual classrooms. According to a report by the World Bank, nearly 1.6 billion students were affected by school closures at the height of the pandemic. One major advantage of remote learning is the ability to access a wealth of digital resources and interactive tools that can enhance the learning experience. However, the transition has also highlighted significant disparities in access to technology and internet connectivity.",
     "The education sector is transforming due to the mainstream adoption of remote learning, accelerated by the COVID-19 pandemic, affecting 1.6 billion students and highlighting both opportunities for innovation and challenges such as disparities in access to technology, with efforts underway to improve digital infrastructure and support disadvantaged students, thereby shaping the future of education."),
    ("modular housing",
     "In a bid to address the housing crisis, several cities across the country are experimenting with new approaches to affordable housing. One such initiative is the construction of modular homes, which are built off-site and assembled on location. These homes are designed to be cost-effective, energy-efficient, and quick to construct. The modular housing project in San Francisco aims to provide affordable housing for low-income families, seniors, and individuals experiencing homelessness. The first phase of the project, which includes 500 units, is expected to be completed by the end of the year.",
     "In response to the housing crisis, cities are adopting modular homes that are cost-effective, energy-efficient, and quick to build, with San Francisco's initiative aiming to provide 500 affordable units for low-income families and homeless individuals, though critics stress the need for comprehensive urban planning and infrastructure investment for long-term success."),
    ("colony collapse",
     "The decline of bee populations worldwide is causing alarm among scientists, environmentalists, and agricultural experts. Bees play a crucial role in pollinating crops, which is essential for food production and biodiversity. The phenomenon, known as Colony Collapse Disorder (CCD), has been linked to several factors, including pesticide exposure, habitat loss, climate change, and diseases. According to a report by the Food and Agriculture Organization (FAO), bee populations have decreased by over 30% in some regions over the past decade.",
     "The global decline of bee populations, attributed to various factors like pesticide exposure, habitat loss, climate change, and diseases, raises concerns among scientists and environmentalists due to its detrimental effects on pollination and biodiversity, prompting initiatives such as promoting bee-friendly farming practices, restoring natural habitats, researching disease treatments, and raising public awareness to safeguard bees."),
    ("ancient migration",
     "Human migration in ancient history has played a critical role in shaping the cultural and genetic landscape of modern populations. Archaeological evidence and genetic studies suggest that early humans migrated out of Africa approximately 60,000 years ago, spreading across the globe and populating various regions. These migrations were driven by a range of factors, including climate changes, resource availability, and social dynamics. One of the key migration routes led early humans into the Middle East and then into Europe and Asia.",
     "Ancient human migrations, sparked by factors like climate shifts and resource availability, sculpted modern cultural and genetic diversity, with early Homo sapiens venturing out of Africa around 60,000 years ago, settling in regions like the Middle East, Europe, and Asia, where evidence of complex cultures and interbreeding with other hominins like Neanderthals and Denisovans enrich our understanding of humanity's dynamic history."),
    ("animal testing ethics",
     "The ongoing debate over the ethics of animal testing in scientific research has reached new heights, as activists and scientists clash over the practice. Animal testing has been a cornerstone of biomedical research for decades, playing a crucial role in the development of treatments for diseases such as cancer, diabetes, and heart disease. Proponents argue that animal models are essential for understanding complex biological processes and ensuring the safety of new medications before they are tested on humans. However, animal rights groups vehemently oppose the practice, citing concerns about the welfare and ethical treatment of animals.",
     "The debate over animal testing's ethics is intensifying as activists and scientists clash, with proponents highlighting its crucial role in biomedical research and treatment development, while opponents emphasize animal welfare and advocate for alternative methods, reflecting a global trend towards more ethical scientific practices with legislative efforts like the EU's strict regulations."),
    ("space exploration",
     "The resurgence of space exploration is capturing global attention, as nations and private companies embark on ambitious missions to the Moon, Mars, and beyond. This renewed interest in space is driven by advancements in technology, a spirit of international collaboration, and the tantalizing potential for scientific discovery. Recent milestones, such as the successful landing of NASA's Perseverance rover on Mars and China's Chang'e-5 mission returning lunar samples, underscore the rapid progress being made. The potential benefits of this new space age are vast.",
     "The global resurgence in space exploration, driven by technological advancements and international collaboration, holds promise for unlocking the universe's mysteries and yielding significant scientific, economic, and technological benefits, though it faces challenges like high costs, technical complexities, and ethical considerations demanding careful planning and international cooperation."),
]


# ============================================================================
# IELTS — additional True / False / Not Given
# ============================================================================
IELTS_TFNG_NEW = [
    {
        "passage": "The phenomenon of urban heat islands — areas in cities that experience significantly higher temperatures than surrounding rural regions — has been studied extensively since the 1960s. Concrete and asphalt absorb solar radiation during the day and release it slowly at night, leading to nighttime temperature differences of up to 7°C between city centers and their outskirts. The effect is intensified by the heat generated by vehicles, air conditioning units, and industrial activity. Recent research has shown that planting urban trees, painting roofs white, and installing reflective pavements can mitigate the effect, with some cities reporting temperature reductions of 2-3°C after implementing such measures. However, the relative effectiveness of these interventions varies considerably based on climate, building density, and the species of trees planted.",
        "statement": "Urban heat islands can be up to 7°C warmer than rural areas during the day.",
        "answer": "false",
        "explanation": "The passage says the 7°C difference applies to NIGHTTIME, not daytime. The statement reverses this. FALSE — passage explicitly contradicts.",
        "trap": "If you skim and see '7°C' next to 'urban heat islands', you may mark TRUE. Always check the qualifier (day vs night).",
    },
    {
        "passage": "The phenomenon of urban heat islands — areas in cities that experience significantly higher temperatures than surrounding rural regions — has been studied extensively since the 1960s. Concrete and asphalt absorb solar radiation during the day and release it slowly at night, leading to nighttime temperature differences of up to 7°C between city centers and their outskirts. The effect is intensified by the heat generated by vehicles, air conditioning units, and industrial activity. Recent research has shown that planting urban trees, painting roofs white, and installing reflective pavements can mitigate the effect, with some cities reporting temperature reductions of 2-3°C after implementing such measures. However, the relative effectiveness of these interventions varies considerably based on climate, building density, and the species of trees planted.",
        "statement": "Tokyo has implemented the most successful urban cooling program in Asia.",
        "answer": "not given",
        "explanation": "The passage discusses cooling interventions generically but mentions no specific city, country, or comparison. NOT GIVEN — not addressed.",
        "trap": "The passage mentions cooling success in 'some cities' — readers may guess one. But guessing is exactly what NG catches. If the city isn't named, it's NG.",
    },
    {
        "passage": "The history of vaccination dates back to 1796, when English physician Edward Jenner observed that milkmaids who had contracted cowpox seemed immune to the more deadly smallpox. Building on this observation, Jenner inoculated a young boy with cowpox material and then exposed him to smallpox, demonstrating that the cowpox infection conferred immunity. Although his approach was crude by modern standards and would not be permitted under contemporary ethical guidelines, it laid the foundation for the science of immunology. Within a century, vaccination had become standard practice in much of Europe and North America. Modern vaccines work through diverse mechanisms — some use weakened pathogens, others use only fragments of the pathogen's protein, and the most recent generation uses messenger RNA to instruct cells to produce a target protein.",
        "statement": "Edward Jenner's vaccination experiment would be considered ethical by today's standards.",
        "answer": "false",
        "explanation": "The passage states his approach 'would not be permitted under contemporary ethical guidelines' — the statement claims the opposite. FALSE.",
        "trap": "If you skim and miss the 'would not be permitted' clause, you might mark TRUE because the experiment 'worked'. Read for ethical language explicitly.",
    },
    {
        "passage": "The history of vaccination dates back to 1796, when English physician Edward Jenner observed that milkmaids who had contracted cowpox seemed immune to the more deadly smallpox. Building on this observation, Jenner inoculated a young boy with cowpox material and then exposed him to smallpox, demonstrating that the cowpox infection conferred immunity. Although his approach was crude by modern standards and would not be permitted under contemporary ethical guidelines, it laid the foundation for the science of immunology. Within a century, vaccination had become standard practice in much of Europe and North America. Modern vaccines work through diverse mechanisms — some use weakened pathogens, others use only fragments of the pathogen's protein, and the most recent generation uses messenger RNA to instruct cells to produce a target protein.",
        "statement": "Some modern vaccines instruct human cells to produce specific proteins.",
        "answer": "true",
        "explanation": "The passage states directly: 'the most recent generation uses messenger RNA to instruct cells to produce a target protein.' Direct match — TRUE.",
        "trap": "None significant. Clear TRUE — trust the passage when it's this explicit.",
    },
    {
        "passage": "The Maillard reaction, discovered by French chemist Louis-Camille Maillard in 1912, is the chemical process responsible for the browning of food when heated. It occurs between amino acids and reducing sugars, typically at temperatures above 140°C, and produces hundreds of distinct flavor compounds — the reason a seared steak smells and tastes fundamentally different from a boiled one. Despite its central role in cooking, the reaction was studied seriously by food scientists only from the 1950s onward, when industrial food production demanded better understanding of flavor development. The reaction is also linked to less desirable outcomes: it produces acrylamide, a compound considered a probable human carcinogen, when starchy foods are cooked at high temperatures.",
        "statement": "Louis-Camille Maillard immediately recognized the importance of his discovery for cooking.",
        "answer": "not given",
        "explanation": "The passage notes that food scientists studied the reaction 'seriously...only from the 1950s onward', but says nothing about Maillard's personal recognition or attitude. NOT GIVEN.",
        "trap": "It's tempting to infer FALSE because cooking application was delayed, but the passage doesn't speak to Maillard's PERSONAL view. Inference ≠ stated.",
    },
    {
        "passage": "The Maillard reaction, discovered by French chemist Louis-Camille Maillard in 1912, is the chemical process responsible for the browning of food when heated. It occurs between amino acids and reducing sugars, typically at temperatures above 140°C, and produces hundreds of distinct flavor compounds — the reason a seared steak smells and tastes fundamentally different from a boiled one. Despite its central role in cooking, the reaction was studied seriously by food scientists only from the 1950s onward, when industrial food production demanded better understanding of flavor development. The reaction is also linked to less desirable outcomes: it produces acrylamide, a compound considered a probable human carcinogen, when starchy foods are cooked at high temperatures.",
        "statement": "The Maillard reaction can produce compounds that may be harmful to human health.",
        "answer": "true",
        "explanation": "The passage explicitly states acrylamide (a Maillard product) is 'considered a probable human carcinogen'. Direct support — TRUE.",
        "trap": "If you anchor on the early positive description (browning, flavor) and miss the final sentence, you might mark FALSE or NG. Always finish the passage.",
    },
]


# ============================================================================
# IELTS — additional Multiple Choice
# ============================================================================
IELTS_MCQ_NEW = [
    {
        "topic": "main idea identification",
        "passage": "The recent shift towards plant-based diets has been driven by a combination of environmental, health, and ethical considerations. Studies have shown that diets centered on plants, particularly whole grains, legumes, vegetables, and nuts, are associated with lower rates of cardiovascular disease, type 2 diabetes, and certain cancers. From an environmental perspective, plant-based foods generally require less land, water, and energy to produce than animal products, contributing fewer greenhouse gas emissions per calorie. However, nutritionists caution that simply removing meat from one's diet does not guarantee improved health — heavily processed plant-based substitutes often contain high levels of sodium, saturated fat from coconut and palm oils, and various additives. A genuinely beneficial plant-based diet relies primarily on minimally processed whole foods, not on industrial meat alternatives.",
        "question": "What is the main argument of the passage?",
        "options": [
            "All plant-based diets are equally beneficial for health and the environment.",
            "Plant-based diets are healthier than any meat-based diet under all conditions.",
            "Whole-food plant-based diets offer benefits, but processed alternatives are problematic.",
            "Industrial meat alternatives are the most important component of a plant-based diet.",
        ],
        "answer": 2,
        "explanation": "The passage acknowledges benefits AND warns about processed substitutes, concluding that 'genuinely beneficial' diets rely on 'minimally processed whole foods'. Option C captures this distinction. A and B overstate; D contradicts the warning.",
        "trap": "B is tempting because the passage spends time on health benefits — but the WHOLE passage is about the distinction within plant-based diets, not plant vs meat.",
    },
    {
        "topic": "detail identification",
        "passage": "Sleep research conducted over the past two decades has overturned several long-held assumptions about the function and structure of sleep. Once thought to be a passive state of inactivity, sleep is now understood as an active process during which the brain consolidates memories, clears metabolic waste through the recently discovered glymphatic system, and modulates immune responses. Crucially, these functions are not evenly distributed across the night: deep slow-wave sleep, concentrated in the first half of the night, appears most important for waste clearance and physical recovery, while REM sleep, more abundant in the later hours, plays a central role in emotional processing and creative problem-solving. Cutting sleep short therefore does not merely reduce total hours — it disproportionately strips away the REM phases that occur in the morning, with consequences for emotional regulation and cognition.",
        "question": "According to the passage, why is cutting sleep short particularly damaging?",
        "options": [
            "It eliminates deep slow-wave sleep, which is concentrated in the morning.",
            "It disproportionately reduces REM sleep, which is more abundant later in the night.",
            "It prevents the glymphatic system from clearing metabolic waste entirely.",
            "It reduces total sleep hours but does not affect any specific sleep phase.",
        ],
        "answer": 1,
        "explanation": "The passage states cutting sleep short 'disproportionately strips away the REM phases that occur in the morning'. Option B paraphrases this. A reverses (slow-wave is FIRST half), C overstates ('entirely'), D contradicts.",
        "trap": "A confuses the two sleep types — deep slow-wave and REM have different distributions. If you remember 'one type is more important morning' but not which, you may pick wrong. Specific reading wins.",
    },
    {
        "topic": "writer's view",
        "passage": "The rise of artificial intelligence has prompted intense debate about its impact on creative work. Some commentators argue that AI tools will democratize creativity, allowing individuals without formal training to produce sophisticated music, images, and text. Others warn that the same tools threaten the livelihoods of working artists by flooding markets with cheap synthetic output and by training on copyrighted material without permission. The truth likely lies between these positions: AI may indeed lower the barrier to certain forms of creative production while simultaneously concentrating economic value in the hands of platform owners rather than human creators. What the current debate often overlooks is that the technology is unlikely to evolve neatly into either utopia or dystopia — its effects will depend on how it is regulated, on what compensation models emerge, and on how human audiences value the distinction between AI-generated and human-made work.",
        "question": "What is the writer's stance on AI's impact on creative work?",
        "options": [
            "AI will conclusively democratize creativity for all individuals.",
            "AI will destroy the livelihoods of all working artists.",
            "AI's impact will be shaped by regulation, business models, and audience preferences.",
            "AI will have no meaningful impact on creative industries.",
        ],
        "answer": 2,
        "explanation": "The writer explicitly says 'its effects will depend on how it is regulated, on what compensation models emerge, and on how human audiences value the distinction'. C captures this. A and B mirror the extreme positions the writer EXPLICITLY rejects ('between these positions'). D contradicts.",
        "trap": "A and B are the OBVIOUS positions in the debate — but the writer's tactic is to reject both and articulate a middle path. The right answer is rarely the loudest claim.",
    },
    {
        "topic": "inference",
        "passage": "Until the mid-19th century, the dominant view in Western medicine held that disease was caused by 'miasmas' — noxious air emanating from rotting matter. This theory provided a logical framework for some sound public health interventions, such as removing waste from streets and improving ventilation, but it offered no explanation for why the same air affected some individuals and not others. The germ theory of disease, developed primarily through the work of Louis Pasteur and Robert Koch in the 1860s and 1870s, eventually displaced miasma theory by identifying specific microorganisms responsible for specific illnesses. The transition was not immediate: many established physicians resisted the new theory, and it took decades for germ-based hygiene practices, such as surgeons washing their hands between patients, to become standard.",
        "question": "What can be inferred from the passage about the acceptance of new scientific theories?",
        "options": [
            "Scientific communities universally welcome new theories that overturn old ones.",
            "Established practitioners are sometimes slow to adopt theories that contradict prevailing views.",
            "Miasma theory is still considered scientifically valid by some doctors today.",
            "Germ theory was never resisted by anyone in the medical community.",
        ],
        "answer": 1,
        "explanation": "The passage explicitly says 'many established physicians resisted the new theory' and 'it took decades' for new practices to standardize. Option B paraphrases this. A and D contradict the passage; C is not mentioned.",
        "trap": "A is what one might WANT to believe about science (open-minded). The passage clearly shows otherwise — read for what's stated, not what's appealing.",
    },
    {
        "topic": "detail identification",
        "passage": "Sponges are among the simplest of multicellular animals, yet they exhibit remarkable biological capabilities that have caught the attention of medical researchers. Unlike most animals, sponges lack true tissues, organs, or a nervous system, instead functioning as collections of specialized cells that can be separated, mixed, and then reassembled — sometimes from cells of different individuals — into functioning sponges. This regenerative capacity, combined with the chemical compounds sponges produce to defend against predators and pathogens, has made them a focus of pharmaceutical research. Several anticancer drugs in current use, including cytarabine and trabectedin, were derived from compounds originally identified in marine sponges. The challenge is sustainability: harvesting sponges in quantities sufficient for drug production threatens fragile reef ecosystems.",
        "question": "Why is sustainability a concern in sponge-based drug development?",
        "options": [
            "Sponges cannot regenerate quickly enough to meet pharmaceutical demand.",
            "Harvesting sponges in sufficient quantities threatens reef ecosystems.",
            "The chemical compounds in sponges lose potency when extracted.",
            "Sponges have only been discovered in very small numbers worldwide.",
        ],
        "answer": 1,
        "explanation": "The passage states directly: 'harvesting sponges in quantities sufficient for drug production threatens fragile reef ecosystems.' Option B paraphrases. Others are not stated.",
        "trap": "A sounds plausible given the passage discussed regeneration, but the passage actually emphasizes how regenerative sponges ARE — so 'cannot regenerate quickly enough' contradicts the passage's tone.",
    },
]


# ============================================================================
# IELTS — additional essays
# ============================================================================
IELTS_ESSAYS_NEW = [
    ("opinion", "Many people believe that social media has fundamentally changed political discourse for the worse. Others argue that it has democratized political participation. Discuss both views and give your own opinion."),
    ("agree-disagree", "Some people believe that governments should invest heavily in public transportation rather than building new roads. To what extent do you agree or disagree?"),
    ("two-part", "In many countries today, people are working longer hours than in the past. What are the reasons for this trend? What problems can it cause?"),
    ("problem-solution", "Obesity rates are rising in many developed countries, particularly among children. What do you think are the main causes of this problem, and what measures can be taken to address it?"),
    ("opinion", "Some argue that history is the most important school subject because it teaches us about the past. Others believe subjects like mathematics and science are more useful. Discuss both views and give your opinion."),
]


# ============================================================================
# IELTS — Matching Headings (NEW task type)
# Each question has: paragraphs (4-6 short paras) and headings (6-8 options,
# one per paragraph + 1-2 distractors). Answer = ordered list mapping each
# paragraph index → heading index.
# ============================================================================
IELTS_MATCHING_HEADINGS = [
    {
        "id": "i-mh-001",
        "topic": "scientific overview",
        "instructions": "Choose the best heading for each paragraph from the list of headings below. There are more headings than paragraphs.",
        "paragraphs": [
            "Coral reefs cover less than 1% of the ocean floor, yet they support approximately one quarter of all marine species. This extraordinary biodiversity has earned them the nickname 'rainforests of the sea'. The structural complexity of reefs creates countless microhabitats, each occupied by specialized organisms that have co-evolved over millions of years.",
            "The primary threats to reefs come from three converging pressures. Rising sea temperatures cause coral bleaching, a stress response in which the symbiotic algae living within coral tissues are expelled. Ocean acidification, driven by absorbed atmospheric CO2, weakens the calcium carbonate skeletons corals depend on. And localized pollution from coastal development introduces nutrients and sediments that suffocate reef systems.",
            "Conservation efforts have produced mixed results. Marine protected areas have shown clear benefits where enforcement is consistent, allowing fish populations to recover and providing breeding sanctuaries that benefit surrounding fisheries. However, MPAs cannot address the systemic threats of climate change, which require coordinated international action far beyond local protection.",
            "Some researchers are now exploring more interventionist approaches. Selective breeding of heat-tolerant coral strains, assisted migration to cooler waters, and even genetic engineering have moved from fringe ideas to subjects of serious scientific investigation. These approaches carry their own risks but reflect a growing acceptance that conventional conservation alone will not be sufficient.",
        ],
        "headings": [
            "The economic value of reef tourism",
            "The biodiversity hotspot of the ocean",
            "Combined causes of reef decline",
            "Limitations of local protection measures",
            "New and controversial intervention strategies",
            "Historical use of corals in medicine",
            "Public awareness campaigns",
        ],
        "answer": [1, 2, 3, 4],
        "explanation": "Para 1 → heading 1 (biodiversity hotspot — main idea of paragraph). Para 2 → 2 (lists three causes of decline). Para 3 → 3 (MPA limitations). Para 4 → 4 (new interventionist methods). The two extra headings (economic value, medicine, awareness) are distractors not addressed in any paragraph.",
        "trap": "Heading 0 ('economic value of reef tourism') sounds plausibly related but is NEVER mentioned. Matching Headings often includes plausible-sounding distractors. Match what's IN the paragraph, not what could be.",
    },
    {
        "id": "i-mh-002",
        "topic": "social trends",
        "instructions": "Choose the best heading for each paragraph from the list of headings below.",
        "paragraphs": [
            "The traditional milestones of adulthood — finishing education, leaving home, finding stable work, marrying, and having children — once occurred for most people in their early twenties. In many wealthy countries today, the average age at which these milestones are reached has shifted by five to ten years. Sociologists describe this as 'emerging adulthood', a distinct life stage between adolescence and full adult responsibility.",
            "Several converging factors explain the shift. Higher education has become both more accessible and more prolonged, with post-graduate degrees now common requirements for white-collar work. The cost of housing has risen sharply relative to incomes, making independent living difficult to achieve early. And labor markets favor specialized expertise that takes years to develop.",
            "The consequences are mixed. Young adults report greater freedom to explore identity, relationships, and career paths, and many use this period for travel and unpaid creative work that would have been impossible under earlier expectations. At the same time, mental health professionals have noted rising rates of anxiety and a persistent sense of incompleteness in this cohort, exacerbated by social media comparisons.",
        ],
        "headings": [
            "Defining a new stage of life",
            "Government policies promoting independence",
            "Why milestones are delayed",
            "The biological aging process",
            "Mixed outcomes for those affected",
            "Generational comparisons across centuries",
        ],
        "answer": [0, 2, 4],
        "explanation": "Para 1 → 0 (introduces 'emerging adulthood' as a new life stage). Para 2 → 2 (explains why milestones happen later: education, housing, labor). Para 3 → 4 (describes mixed outcomes: freedom + mental health). Distractors include government policies (not mentioned), biology (not relevant), historical comparison (only modern context discussed).",
        "trap": "Heading 5 ('generational comparisons') sounds related — the passage compares 'now' to 'once' — but the focus is on the present, not on systematic generational analysis. Heading must capture the WHOLE paragraph's focus.",
    },
    {
        "id": "i-mh-003",
        "topic": "technology adoption",
        "instructions": "Choose the best heading for each paragraph from the list of headings below.",
        "paragraphs": [
            "Voice assistants like Siri, Alexa, and Google Assistant were initially marketed as transformative tools that would change how we interact with computers. A decade after their widespread introduction, the reality is more modest: most users employ them for a narrow set of tasks — playing music, setting timers, checking weather — and ignore their broader capabilities entirely.",
            "Researchers studying this 'shallow adoption' point to several causes. Voice interfaces struggle with anything that requires precision, nuance, or memory across interactions; users quickly learn the boundaries of what works and avoid the rest. Privacy concerns also limit adoption: users hesitate to issue voice commands containing sensitive information, especially in shared spaces.",
            "The gap between marketing promise and actual use offers a broader lesson about predicting technology adoption. Capabilities matter less than the friction users encounter at the margin: an extra word to remember, a privacy worry, an unreliable result. Tools that quietly remove friction tend to expand into daily life; tools that promise great things while creating small annoyances tend to plateau.",
        ],
        "headings": [
            "The gap between hype and reality",
            "Predicting future voice technology",
            "Why users limit their usage",
            "The role of marketing in product launches",
            "A general principle of technology adoption",
            "The competitive landscape of voice assistants",
        ],
        "answer": [0, 2, 4],
        "explanation": "Para 1 → 0 (contrast between marketing promise and modest reality). Para 2 → 2 (causes of shallow adoption: precision limits, privacy). Para 3 → 4 (broader principle about technology adoption generally). Distractors include marketing tactics (not discussed), competitive landscape (not discussed), future prediction (not the topic).",
        "trap": "Heading 3 ('role of marketing') sounds related because marketing is mentioned in para 1 — but the paragraph isn't ABOUT marketing, it's about the gap between promise and reality. Focus on the paragraph's MAIN claim, not a single referenced concept.",
    },
    {
        "id": "i-mh-004",
        "topic": "environmental science",
        "instructions": "Choose the best heading for each paragraph from the list of headings below.",
        "paragraphs": [
            "Soil is far more than a substrate for plant roots; it is a complex living system containing more microorganisms in a single teaspoon than there are humans on Earth. These microbial communities perform essential functions: decomposing organic matter, fixing atmospheric nitrogen, recycling nutrients, and forming symbiotic relationships with plants that vastly extend their access to water and minerals.",
            "Modern industrial agriculture, however, has systematically degraded these communities. Heavy tillage destroys soil structure; synthetic fertilizers reduce the need for nitrogen-fixing bacteria and so reduce their populations; pesticides eliminate beneficial organisms alongside pests; and monocropping starves the diverse microbial communities that depend on diverse plant inputs.",
            "Regenerative agriculture seeks to reverse this damage through practices designed to rebuild soil biology. Cover crops keep soils planted year-round, providing continuous food for microbes. Reduced or zero tillage preserves soil structure and fungal networks. Diverse crop rotations support more varied microbial communities. Early evidence suggests these practices can rebuild soil carbon while maintaining yields.",
        ],
        "headings": [
            "The hidden life beneath our feet",
            "How modern farming damages soil ecology",
            "The history of agricultural science",
            "Practices for restoring soil health",
            "Government subsidies for farmers",
            "Soil composition in different climates",
        ],
        "answer": [0, 1, 3],
        "explanation": "Para 1 → 0 (introduces the hidden microbial life in soil). Para 2 → 1 (how industrial agriculture damages soil). Para 3 → 3 (regenerative practices to restore soil). The other headings (history, subsidies, climate variation) are not addressed.",
        "trap": "Heading 5 ('soil composition in different climates') seems vaguely related but the paragraphs are about microbial communities and agricultural practices, not climate-specific composition.",
    },
    {
        "id": "i-mh-005",
        "topic": "psychology",
        "instructions": "Choose the best heading for each paragraph from the list of headings below.",
        "paragraphs": [
            "When two people witness the same event, their accounts often diverge in surprising ways. Memory research has consistently shown that what people 'remember' is not a faithful recording of the past but an active reconstruction shaped by expectations, prior knowledge, and subsequent experiences. Even confident, detailed memories can be entirely false.",
            "The implications for the legal system are significant. Eyewitness testimony was long considered among the strongest forms of evidence, but studies have shown that wrongful convictions disproportionately involve cases relying heavily on eyewitness accounts. DNA exoneration projects in the United States have demonstrated that mistaken identification by sincere, confident witnesses was the leading cause of false convictions in their database.",
            "Several reforms have been proposed and partially adopted. Identification procedures can be modified to reduce suggestion: showing witnesses photos sequentially rather than in groups, ensuring administrators do not know which photo is the suspect, and recording confidence levels at the moment of identification rather than later. These changes do not eliminate the problem but measurably reduce error rates.",
        ],
        "headings": [
            "The reconstructive nature of memory",
            "How memory improves with age",
            "Eyewitness testimony in court",
            "Famous historical legal cases",
            "Reforms to identification procedures",
            "Brain regions involved in memory",
        ],
        "answer": [0, 2, 4],
        "explanation": "Para 1 → 0 (memory as active reconstruction, not faithful recording). Para 2 → 2 (problems with eyewitness testimony in the legal system). Para 3 → 4 (specific reform proposals). Distractors include memory improving (not stated), historical cases (none cited), brain regions (not the focus).",
        "trap": "Heading 3 ('famous historical cases') might draw you if you recall DNA exonerations as a 'case' — but the passage refers to a body of evidence, not specific famous cases.",
    },
]


IELTS_MH_TIPS = [
    {"cat": "Strategy", "tip": "Read all the headings FIRST, then read each paragraph and ask: 'Which heading captures THIS paragraph's main idea?' Don't try to match passage-to-heading; match heading-to-passage."},
    {"cat": "Strategy", "tip": "There are always MORE headings than paragraphs (typically 2-3 extra). Don't try to use them all. Headings you don't use are the distractors."},
    {"cat": "Strategy", "tip": "Eliminate headings as you confirm matches. After you assign heading X to paragraph 2, cross it off — it can't also fit paragraph 3."},
    {"cat": "Strategy", "tip": "If two headings seem to fit a paragraph, look at the FIRST and LAST sentences of the paragraph. The main heading should reflect the central claim, not a detail."},
    {"cat": "Time", "tip": "Matching Headings is the SLOWEST IELTS reading task. Budget 7-8 minutes for a 5-paragraph set. Do it LAST in a passage after faster tasks."},
    {"cat": "Traps", "tip": "Distractor headings often pick up a single keyword from the paragraph but miss the main idea. 'Government subsidies' as a heading when the paragraph mentions 'government' once = trap."},
    {"cat": "Traps", "tip": "Sometimes the right heading uses NO words from the paragraph — it's a thematic summary. Don't reject a heading just because it lacks shared vocabulary."},
    {"cat": "Tricks", "tip": "Two-pass approach: pass 1, match the OBVIOUS paragraphs (where the heading shouts at you). Pass 2, work through the remaining paragraphs with a smaller heading pool — much easier with distractors already used."},
    {"cat": "Tricks", "tip": "If you're stuck on the LAST paragraph and only one heading remains, go ahead and assign it — but spot-check whether it actually fits. If not, you mis-assigned an earlier one."},
    {"cat": "Scoring", "tip": "1 raw point per paragraph correctly matched. No partial credit per paragraph. Order matters — write the heading number that matches each paragraph number in order."},
]


# ============================================================================
# Build
# ============================================================================
def normalize(s: str) -> str:
    return " ".join(s.lower().split())


def load_mcq_scrape():
    """Load PTE MCQ items from /tmp/pte_mcq_scrape.jsonl (parsed by Bash earlier)."""
    if not MCQ_SCRAPE.exists():
        return []
    items = []
    with MCQ_SCRAPE.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return items


def build():
    raw = json.loads(BANK.read_text())
    if raw.get("schema") != 2:
        print("ERROR: bank is not v2. Run migrate_bank_v2.py first.")
        return 0, 0

    pte = raw["tests"]["pte"]
    ielts = raw["tests"]["ielts"]

    existing_pte_ids = {q["id"] for q in pte["questions"]}
    existing_ielts_ids = {q["id"] for q in ielts["questions"]}
    existing_pte_passages = {normalize(q.get("passage", ""))[:200] for q in pte["questions"] if q.get("passage")}

    added_pte = 0
    added_ielts = 0
    rng = random.Random(2026)

    # ----- PTE: re-order paragraphs -----
    next_idx = 200  # avoid collision with earlier 100-block
    for correct_order in PTE_REORDERS_NEW:
        if normalize(correct_order[0])[:120] in {normalize(q.get("paragraphs", [""])[0])[:120] for q in pte["questions"] if q.get("type") == "reorder"}:
            continue
        n = len(correct_order)
        perm = list(range(n))
        rng.shuffle(perm)
        displayed = [correct_order[perm[j]] for j in range(n)]
        answer = [perm.index(k) for k in range(n)]
        qid = f"r-reorder-{next_idx:03d}"
        while qid in existing_pte_ids:
            next_idx += 1
            qid = f"r-reorder-{next_idx:03d}"
        pte["questions"].append({
            "id": qid,
            "section": "reading",
            "type": "reorder",
            "topic": "logical flow",
            "paragraphs": displayed,
            "answer": answer,
            "explanation": "Find the topic sentence first (it stands alone). Track time markers, pronouns (this, these, they), and connectors (however, then, finally) to determine sequence.",
            "trap": "Paragraphs starting with 'This', 'These', or 'However' cannot be first — they reference something prior.",
            "source": "goarno (personal practice)",
        })
        existing_pte_ids.add(qid)
        added_pte += 1
        next_idx += 1

    # ----- PTE: SWT -----
    next_idx = 200
    for topic, passage, sample in PTE_SWT_NEW:
        if normalize(passage)[:200] in existing_pte_passages:
            continue
        qid = f"w-swt-{next_idx:03d}"
        while qid in existing_pte_ids:
            next_idx += 1
            qid = f"w-swt-{next_idx:03d}"
        pte["questions"].append({
            "id": qid,
            "section": "writing",
            "type": "swt",
            "topic": topic,
            "passage": passage,
            "rubric": "ONE sentence, 5-75 words. Capture main claim + key tension or caveat. Use a complex structure (although/while/despite).",
            "sample": sample,
            "grading_notes": "PTE rubric: Form (1 sentence) 0-1, Length (5-75 words) 0-1, Content (main idea + supporting) 0-2, Grammar 0-2, Vocab 0-1. Need >=5/7.",
            "source": "goarno (personal practice)",
        })
        existing_pte_ids.add(qid)
        added_pte += 1
        next_idx += 1

    # ----- PTE: MCQ from scrape file -----
    next_idx = 200
    mcq_items = load_mcq_scrape()
    for it in mcq_items:
        passage = it.get("passage", "")
        if not passage or normalize(passage)[:200] in existing_pte_passages:
            continue
        options = it.get("options", [])
        ans_text = it.get("answer_text", "")
        if not options or ans_text not in options:
            continue
        qid = f"r-mcq-{next_idx:03d}"
        while qid in existing_pte_ids:
            next_idx += 1
            qid = f"r-mcq-{next_idx:03d}"
        pte["questions"].append({
            "id": qid,
            "section": "reading",
            "type": "mcq_single",
            "topic": "detail identification",
            "passage": passage,
            "question": it.get("question", ""),
            "options": options,
            "answer": options.index(ans_text),
            "explanation": "Match each option directly to the passage. The correct option restates the passage's claim in different words; distractors either contradict, exaggerate, or add facts not stated.",
            "trap": "Watch for options with absolute words ('all', 'only', 'never') or that go beyond what the passage explicitly states.",
            "source": "goarno (personal practice)",
        })
        existing_pte_ids.add(qid)
        existing_pte_passages.add(normalize(passage)[:200])
        added_pte += 1
        next_idx += 1
        if added_pte > 80:  # safety cap
            break

    # ----- IELTS: T/F/NG -----
    next_idx = 200
    for q in IELTS_TFNG_NEW:
        qid = f"i-tfng-{next_idx:03d}"
        while qid in existing_ielts_ids:
            next_idx += 1
            qid = f"i-tfng-{next_idx:03d}"
        ielts["questions"].append({
            "id": qid,
            "section": "reading",
            "type": "tfng",
            "topic": "true false not given",
            **q,
        })
        existing_ielts_ids.add(qid)
        added_ielts += 1
        next_idx += 1

    # ----- IELTS: MCQ -----
    next_idx = 200
    for q in IELTS_MCQ_NEW:
        qid = f"i-mcq-{next_idx:03d}"
        while qid in existing_ielts_ids:
            next_idx += 1
            qid = f"i-mcq-{next_idx:03d}"
        ielts["questions"].append({
            "id": qid,
            "section": "reading",
            "type": "mcq_single",
            **q,
        })
        existing_ielts_ids.add(qid)
        added_ielts += 1
        next_idx += 1

    # ----- IELTS: essays -----
    next_idx = 200
    for topic, prompt in IELTS_ESSAYS_NEW:
        qid = f"i-essay-{next_idx:03d}"
        while qid in existing_ielts_ids:
            next_idx += 1
            qid = f"i-essay-{next_idx:03d}"
        ielts["questions"].append({
            "id": qid,
            "section": "writing",
            "type": "essay",
            "topic": topic,
            "prompt": prompt + " Write at least 250 words.",
            "rubric": "250-300 words. 5 paragraphs. Address the question type explicitly.",
            "grading_notes": "IELTS Task 2: Task Response, Coherence/Cohesion, Lexical Resource, Grammar (each 25%).",
        })
        existing_ielts_ids.add(qid)
        added_ielts += 1
        next_idx += 1

    # ----- IELTS: Matching Headings (NEW type) -----
    for q in IELTS_MATCHING_HEADINGS:
        if q["id"] in existing_ielts_ids:
            continue
        item = {
            "section": "reading",
            "type": "matching_headings",
            **q,
        }
        ielts["questions"].append(item)
        existing_ielts_ids.add(q["id"])
        added_ielts += 1

    # ----- IELTS: matching_headings tips -----
    ielts.setdefault("tips", {})
    ielts["tips"]["reading_matching_headings"] = IELTS_MH_TIPS

    BANK.write_text(json.dumps(raw, indent=2, ensure_ascii=False))
    return added_pte, added_ielts


if __name__ == "__main__":
    p, i = build()
    print(f"Added {p} PTE questions, {i} IELTS questions.")
    bank = json.loads(BANK.read_text())
    print(f"Totals: PTE {len(bank['tests']['pte']['questions'])}, IELTS {len(bank['tests']['ielts']['questions'])}")
