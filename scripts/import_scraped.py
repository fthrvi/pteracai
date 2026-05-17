#!/usr/bin/env python3
"""Import scraped PTE questions into data/bank.json.

Source: alfapte.com (WFD) and goarno.io (everything else).
Personal-use practice content only — not redistributed.

Run from project root:  python3 scripts/import_scraped.py
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
BANK = ROOT / "public" / "data" / "bank.json"

# --------------------------------------------------------------------------
# Write From Dictation — sentences only (TTS handles audio at runtime)
# --------------------------------------------------------------------------
WFD_SENTENCES = [
    # alfapte batch
    "Some studies show a link between depression and social media.",
    "The marine environment has been destroyed by pollution and unsustainable development.",
    "Please note that the submission deadline can only be extended in special circumstances.",
    "You can use your laptops in the lecture.",
    "Courses differ mainly in the type of assessments they employ.",
    "A complete bibliography is essential for achieving the highest score.",
    "Please ensure your graph is drawn on a separate sheet.",
    "Active listening is vital for success in this particular course.",
    "Payments can be made with either cash or credit card.",
    "People may be influenced by unexpected data leading to decisions different from their expectations.",
    # goarno batch
    "Scientists are discovering new links between genes and diseases.",
    "The university library contains a substantial collection of maps.",
    "Decision-making skills are crucial for those in management positions.",
    "A list of valid sources must be included in the bibliography.",
    "The history course will be assessed via three written assignments.",
    "You can download the lecture notes from the university website.",
    "Genetic research plays a key role in modern medicine.",
    "Attendance at the weekly tutorial is mandatory for all students.",
    "Please hand in your assignments at the main office.",
    "Students must attend the safety training before entering the lab.",
    "Financial stability is a primary concern for many companies.",
    "Lecture slides are available to download from the website.",
    "Course materials will be available on the library website.",
    "Structural stability is a key concept in civil engineering.",
    "Quiet study areas are located on the top floor.",
    "The professor will discuss the project details in the next lecture.",
    "Recent studies have expanded our knowledge of cell biology.",
    "Collaboration is a key component of the learning process.",
    "Motivation is a key factor in employee productivity.",
    "Practical experience is a vital part of the engineering course.",
    "Students are required to submit their research proposals by Friday.",
    "A balanced schedule allows time for both study and rest.",
    "Clinical research has improved our understanding of genetic diseases.",
    "Customer satisfaction is the primary goal of most businesses.",
    "Statistical results should be presented in a clear and concise manner.",
    "Organizational culture has a significant impact on employee performance.",
    "Regular exercise is essential for maintaining physical and mental health.",
    "The student welfare service is located in the main building.",
    "Genetic variation is essential for the survival of species.",
    "A clear business strategy is essential for sustainable growth.",
    "DNA samples are stored in the laboratory for analysis.",
    "All assignments must be submitted by the end of the term.",
    "Critical thinking is an essential part of the undergraduate curriculum.",
    "Oral presentations are assessed on both content and delivery style.",
    "Students should use academic journals for their research projects.",
    "The new timetable will be posted on the student website.",
    "Electronic devices are not permitted in the examination hall.",
    "The course covers both theoretical and practical aspects of the subject.",
    "Certain bacteria can survive in extremely high temperatures.",
    "The research project involves a significant amount of fieldwork.",
    "Business strategies must be flexible to adapt to market changes.",
    "Effective communication is key to resolving conflicts in the workplace.",
    "The manager's role is to facilitate the team's progress.",
    "The department has organized a trip to the national museum.",
    "The genetic code determines the characteristics of living organisms.",
    "Genetic diversity is crucial for the adaptation of species.",
    "The timetable for next semester will be available shortly.",
]

# --------------------------------------------------------------------------
# Re-order Paragraphs — paragraphs in correct order (we'll shuffle on display)
# --------------------------------------------------------------------------
REORDER_CORRECT_ORDERS = [
    [
        "A local community garden has recently been revitalized by volunteers.",
        "The project, which started last month, has brought together people of all ages.",
        "Residents now enjoy fresh vegetables and beautiful flowers grown in the garden.",
        "This initiative has also helped to reduce neighborhood waste, as composting is a key component of the garden's ecosystem.",
        "The city council has praised the project, noting its positive impact on community spirit and environmental awareness.",
    ],
    [
        "Schools in our district will start the new year with updated technology in classrooms.",
        "Over the summer, tablets and interactive whiteboards were installed across multiple schools.",
        "Teachers have received training on how to integrate these tools into their lessons.",
        "The updates are part of a larger effort to enhance digital literacy among students.",
        "Parents and educators alike are hopeful that these improvements will make learning more engaging and effective.",
    ],
    [
        "In the mid-15th century, a German inventor named Johannes Gutenberg developed the printing press, a machine that allowed books to be mass-produced.",
        "Before this invention, books were written by hand, making them expensive and rare.",
        "Gutenberg's press used movable type, which could be rearranged and reused, to print entire pages at once.",
        "His first major publication was the Gutenberg Bible, which became famous for its high quality and was widely distributed.",
        "The printing press revolutionized the spread of knowledge, making books accessible to a much larger audience and fostering the spread of literacy.",
    ],
    [
        "A new art exhibition opened this weekend at the downtown gallery, featuring works from several regional artists.",
        "The show includes paintings, sculptures, and photographs, all exploring the theme of 'Urban Life.'",
        "Gallery owners hope to draw attention to the vibrant local art scene.",
        "The exhibition is free to the public and will run for the next three months.",
        "School groups and art students are especially encouraged to visit.",
    ],
    [
        "Researchers at the University of Atlanta conducted a six-week study to explore the effects of varying sunlight exposure on the growth of tomato plants.",
        "They divided the plants into two groups: one received eight hours of direct sunlight daily, while the other received only four hours.",
        "Measurements taken weekly showed that the plants with more sunlight exposure had a 30% increase in height and produced more fruit.",
        "The study concluded that increased sunlight significantly enhances the growth and fruit production of tomato plants.",
        "These findings could provide valuable insights for agricultural practices, especially in regions with limited natural light.",
    ],
    [
        "Local farmers faced challenges this season due to unexpected weather conditions.",
        "Heavy rains in early spring followed by a dry summer affected crop yields.",
        "Despite the setbacks, the community market has remained open, featuring products from surrounding areas.",
        "Farmers are adapting by using more sustainable farming techniques.",
        "The agricultural department is offering workshops to help them cope with climate variability.",
    ],
    [
        "Yesterday in the British Parliament, members debated a new bill proposing stricter environmental regulations.",
        "The debate began with the Environment Secretary outlining the benefits of the bill, emphasizing its potential to reduce pollution and protect natural habitats.",
        "Opposition members expressed concerns about the impact of these regulations on businesses, particularly small enterprises.",
        "Several amendments were proposed, aiming to balance environmental goals with economic interests.",
        "After hours of discussion, the debate was adjourned, with a vote scheduled for next week.",
    ],
    [
        "A recent study shows that public transportation usage in the city has increased by 20% over the past year.",
        "Officials attribute the rise to improved service times and cleaner facilities.",
        "Additional buses and trains have been added during peak hours to accommodate the growing number of passengers.",
        "The city plans to continue investing in public transport to encourage more residents to use it.",
        "Environmental groups have applauded this trend, highlighting its benefits for air quality.",
    ],
    [
        "The debate over data privacy focuses on how personal information is collected, used, and protected by companies and governments.",
        "Advocates for stricter data privacy argue that individuals should have more control over their personal information to protect their privacy and prevent misuse.",
        "They call for stronger regulations that require companies to be transparent about data collection and to provide options for users to opt out.",
        "On the other hand, some argue that extensive data collection is necessary for technological advancements and security measures.",
        "They believe that limiting data access could hinder innovation and reduce the effectiveness of services tailored to user preferences.",
    ],
    [
        "To brew coffee using a drip coffee maker, start by measuring out the coffee grounds.",
        "For every cup of coffee, you typically need one tablespoon of grounds.",
        "Place a coffee filter in the basket of the coffee maker and add the measured grounds.",
        "Next, fill the coffee maker's reservoir with cold water; use about six ounces of water for each cup you want to make.",
        "Finally, turn on the machine and wait for the coffee to drip into the pot below.",
    ],
    [
        "Researchers from the Alpine Climate Study Group spent two years studying how temperature changes affect mountain ecosystems.",
        "Data was collected on plant and insect populations across different elevations, showing clear shifts in ecological patterns.",
        "Rising temperatures were linked to earlier plant blooming and changes in insect migration routes.",
        "The study highlights the fragility of mountain ecosystems to even minor climatic shifts.",
        "These insights are crucial for developing adaptive strategies to combat the impacts of global warming in these areas.",
    ],
    [
        "The city's annual festival is set to return next month after being canceled last year due to health concerns.",
        "The event will feature live music, food stalls, and various entertainment activities for all ages.",
        "Safety measures will be in place to ensure the wellbeing of attendees.",
        "Local businesses are looking forward to the boost in customers that the festival traditionally brings.",
        "Tickets are available now, with early bird specials for those who purchase in advance.",
    ],
    [
        "The Greenfield Agricultural Center conducted a season-long experiment to compare the effects of natural and chemical fertilizers on wheat production.",
        "Fields treated with natural fertilizers not only yielded more wheat, but also demonstrated better soil health, as indicated by increased microbial activity.",
        "Conversely, chemical fertilizers showed no significant improvement in yield and had a less positive effect on soil condition.",
        "The results suggest that natural fertilizers could provide a sustainable alternative for crop management.",
        "Farmers might benefit from switching to environmentally friendly practices based on these findings.",
    ],
    [
        "The Eiffel Tower, a global symbol of France, was originally built for the 1889 'Exposition Universelle' held in Paris to celebrate the 100th anniversary of the French Revolution.",
        "Its construction was a remarkable feat, completed in just over two years by 300 workers.",
        "Interestingly, the Eiffel Tower was intended to be a temporary structure, with plans to dismantle it after 20 years.",
        "However, it was saved from demolition when it proved valuable as a radiotelegraph station.",
        "Today, it remains one of the most visited monuments in the world, attracting millions of tourists annually.",
    ],
    [
        "The Berlin Wall, which had divided East and West Berlin since 1961, was unexpectedly opened on November 9, 1989.",
        "This event was triggered by a mistaken announcement that East Germans could cross into West Berlin immediately.",
        "Crowds of East and West Germans climbed onto the wall, celebrating together and starting to break it apart piece by piece.",
        "The fall of the wall marked the beginning of German reunification, which was formally completed less than a year later.",
        "This event symbolized the end of the Cold War and the triumph of freedom over division.",
    ],
    [
        "On July 20, 1969, astronauts Neil Armstrong and Buzz Aldrin became the first humans to land on the moon as part of NASA's Apollo 11 mission.",
        "Their spacecraft, the Eagle, touched down on the lunar surface in an area called the Sea of Tranquility.",
        "Neil Armstrong was the first to step onto the moon, famously saying, 'That's one small step for man, one giant leap for mankind.'",
        "The astronauts collected moon rocks and conducted experiments for over two hours.",
        "They returned safely to Earth, landing in the Pacific Ocean, where they were picked up by a waiting ship.",
    ],
]

# --------------------------------------------------------------------------
# Reading MCQ Single Answer
# --------------------------------------------------------------------------
MCQ_QUESTIONS = [
    {
        "passage": "In today's world, technology is changing everything around us. As we dive deeper into the age of artificial intelligence, robotics, and quantum computing, we need to think carefully about how we use these tools.",
        "question": "According to the text, what is the main challenge policymakers face with the advancement of new technologies?",
        "options": [
            "They must find ways to harness the full potential of AI, robotics, and quantum computing without any restrictions.",
            "They need to develop regulations that ensure technological innovations benefit everyone without compromising privacy and freedom.",
            "The challenge is to entirely focus on the economic benefits of technology while neglecting ethical concerns.",
            "Policymakers are tasked with accelerating the adoption of new technologies to improve societal health and stability.",
            "They must prevent all forms of technological development to protect individual privacy and freedom.",
        ],
        "answer": 1,
        "topic": "policy and technology regulation",
    },
    {
        "passage": "The summit opened with a powerful keynote speech from the UN Secretary-General, emphasizing the urgent need for unity and innovative approaches to address the planet's escalating environmental and health challenges.",
        "question": "What was the primary focus of the keynote speech by the UN Secretary-General at the Global Solutions Summit in Geneva?",
        "options": [
            "Highlighting the need for innovative solutions to combat economic inequality and stabilize global markets.",
            "Emphasizing the urgency of unity and innovative approaches to address environmental and health challenges.",
            "Calling for increased funding and resources towards global health initiatives to prevent future pandemics.",
            "Encouraging nations to adopt new technologies for renewable energy to meet their environmental targets.",
            "Stressing the importance of resolving diplomatic disputes through bilateral meetings during the summit.",
        ],
        "answer": 1,
        "topic": "main idea identification",
    },
    {
        "passage": "In the heart of sustainable urban development lies the integration of green spaces. Parks, gardens, and riversides serve not just as aesthetic enhancements but also play crucial roles in improving air quality.",
        "question": "What role do green spaces play in sustainable urban development, according to the text?",
        "options": [
            "They primarily serve to increase property values within the city.",
            "They enhance urban aesthetics and provide social venues for city residents.",
            "They improve air quality, reduce urban heat, and offer habitats for wildlife, contributing significantly to urban sustainability.",
            "They are useful only for recreational purposes and have minimal impact on the urban environment.",
            "They encourage urban dwellers to adopt more sedentary lifestyles by providing relaxing environments.",
            "They are mostly decorative, with little practical benefit to city infrastructure or sustainability.",
        ],
        "answer": 2,
        "topic": "main idea identification",
    },
    {
        "passage": "Firstly, it's important to understand your garden's environment. Pay attention to how much sun and shade each area receives throughout the day. This will guide you in choosing the right plants.",
        "question": "What is the first step a novice gardener should take to ensure they choose the right plants for their garden?",
        "options": [
            "Start by planting the easiest and most common plants available at the garden center.",
            "Understand the garden's environment, particularly the sun and shade distribution.",
            "Purchase a comprehensive gardening book to study different types of plants and their needs.",
            "Focus primarily on improving soil quality with fertilizers and advanced techniques.",
            "Immediately test the soil quality using a professional service rather than a simple kit.",
        ],
        "answer": 1,
        "topic": "detail identification",
    },
    {
        "passage": "As people move from one country to another, they bring with them their cultures, traditions, and skills, which can enrich the communities they join. For example, in many cities, you can now find a wide variety of restaurants, festivals, and cultural events that reflect this diversity.",
        "question": "What is a significant benefit of global migration according to the text?",
        "options": [
            "It reduces the overall costs of healthcare and education for local residents.",
            "It ensures that all migrants are automatically integrated into the workforce without facing any challenges.",
            "Global migration completely eliminates job shortages in all industries across the host countries.",
            "Migrants contribute to cultural diversity, enriching local communities with different cultures, traditions, and skills.",
            "It leads to an immediate and significant increase in the economic wealth of migrants.",
        ],
        "answer": 3,
        "topic": "detail identification",
    },
    {
        "passage": "Recent studies in nutrition science reveal a strong link between diet and longevity. Researchers have found that diets rich in whole foods, such as fruits, vegetables, whole grains, and lean proteins, can significantly extend life expectancy.",
        "question": "According to recent studies in nutrition science, what is the primary benefit of a diet rich in whole foods?",
        "options": [
            "It enhances mental clarity and focus, leading to improved cognitive performance.",
            "It increases physical strength and stamina, enabling more vigorous exercise routines.",
            "It boosts the immune system specifically to prevent seasonal illnesses.",
            "It significantly extends life expectancy by providing essential nutrients and antioxidants.",
            "It leads to faster weight loss compared to other dietary approaches.",
        ],
        "answer": 3,
        "topic": "detail identification",
    },
    {
        "passage": "The United States faces challenges to its traditional dominance, grappling with internal political divides and external pressures. Additionally, the European Union contends with Brexit and varying national interests, impacting its cohesion.",
        "question": "What are the primary challenges faced by the United States in maintaining its global influence, according to the text?",
        "options": [
            "The United States is facing significant economic downturns that hinder its ability to engage internationally.",
            "Internal political divisions and external pressures are key challenges to the United States' traditional dominance.",
            "The United States struggles mainly with technological advancements that outpace its current capabilities.",
            "Increasing competition from emerging economies is the sole challenge faced by the United States.",
            "Climate change is the primary issue, as it is directly impacting the country's economic policies.",
        ],
        "answer": 1,
        "topic": "detail identification",
    },
    {
        "passage": "One key approach is investing in technology and education. By improving education, people can gain the skills needed for the jobs of tomorrow. Also, supporting new technologies can lead to more innovations.",
        "question": "According to the text, what is a key strategy governments are using to address economic challenges and create job opportunities?",
        "options": [
            "They are focusing on reducing taxes for all businesses to encourage investment and economic stability.",
            "Governments are increasing import tariffs to protect domestic industries and create more jobs locally.",
            "Investing in technology and education is a primary approach to prepare individuals for future job demands and stimulate economic growth.",
            "They are primarily offering direct financial assistance to individuals to reduce unemployment rates quickly.",
            "Governments are enforcing stricter regulations on businesses to ensure more job openings are made available for locals.",
        ],
        "answer": 2,
        "topic": "main idea identification",
    },
    {
        "passage": "Studies show that excessive use of social media can lead to feelings of loneliness and anxiety, especially among young people. There is also a growing divide between those who have access to the internet.",
        "question": "What is a significant negative effect of excessive social media use, as indicated in the text?",
        "options": [
            "It often causes feelings of loneliness and anxiety, especially in young people.",
            "It can lead to increased physical activity and better health outcomes.",
            "It enhances personal relationships and community bonding.",
            "Social media use increases the quality and accuracy of information shared online.",
            "It eliminates social inequalities by providing equal access to digital resources.",
        ],
        "answer": 0,
        "topic": "detail identification",
    },
    {
        "passage": "A team of researchers at the University of Cambridge has developed a new type of solar cell that is significantly more efficient than current models. These cells, made from a material called perovskite, can convert sunlight into electricity with an efficiency of over 30%.",
        "question": "What are the main advantages of the perovskite solar cells developed by the University of Cambridge researchers?",
        "options": [
            "They require rare and expensive materials which ensures exclusivity in production.",
            "They have a higher sunlight-to-electricity conversion efficiency and are cost-effective due to abundant materials.",
            "The cells are primarily focused on reducing the physical size of solar panels for better aesthetic integration in urban areas.",
            "These cells can only convert a specific spectrum of light more efficiently than traditional cells.",
            "They offer enhanced durability and stability in extreme weather conditions compared to other solar cells.",
        ],
        "answer": 1,
        "topic": "detail identification",
    },
    {
        "passage": "One critical takeaway is the importance of early detection and rapid response. Delays in identifying and addressing outbreaks can lead to widespread transmission and overwhelm healthcare systems.",
        "question": "What is a critical lesson learned from recent pandemics regarding the management of public health crises?",
        "options": [
            "Ensuring all citizens have access to personal protective equipment is the most critical step in managing a pandemic.",
            "Comprehensive healthcare reform is necessary to improve the general health of the population.",
            "Early detection and rapid response are crucial to prevent widespread transmission and avoid overwhelming healthcare systems.",
            "Investment in mental health services is the most effective way to handle public health emergencies.",
            "Strict enforcement of international travel bans is essential for controlling disease spread.",
        ],
        "answer": 2,
        "topic": "main idea identification",
    },
]

# --------------------------------------------------------------------------
# Fill in the Blanks (Reading & Writing)
# --------------------------------------------------------------------------
# Already structured as text_parts (N+1 strings) + blanks (N options dicts).
FIB_QUESTIONS = [
    {
        "topic": "sleep and cognition",
        "text_parts": [
            "Sleep is a fundamental biological requirement that is essential for maintaining optimal physical health and cognitive performance. When individuals do not get adequate rest, their ability to concentrate and process information is significantly ",
            ". Studies have shown that sleep deprivation can lead to slower reaction times and impaired judgment. Furthermore, chronic lack of sleep is often associated with a higher risk of developing serious medical conditions. To ensure the brain functions efficiently, it is crucial to ",
            " a consistent sleep schedule. During deep sleep, the body undergoes restorative processes that repair tissues and strengthen the immune system. Consequently, neglecting sleep can have profound ",
            " on overall well-being, affecting both mental clarity and emotional stability. Experts recommend that adults aim for between seven and nine hours of quality sleep each night to fully ",
            " their energy levels.",
        ],
        "blanks": [
            {"options": ["compromised", "enhanced", "maintained", "depleted"], "correct": "compromised"},
            {"options": ["ignore", "prioritize", "preserve", "deplete"], "correct": "prioritize"},
            {"options": ["consequences", "origins", "benefits", "impacts"], "correct": "consequences"},
            {"options": ["restore", "deplete", "maintain", "enhance"], "correct": "restore"},
        ],
    },
    {
        "topic": "wetlands and ecosystems",
        "text_parts": [
            "Despite often being dismissed as mere swamps or wastelands suitable only for drainage and development, wetlands perform ",
            " functions within the global ecosystem. These distinct habitats are ",
            " in filtering pollutants from water and acting as natural sponges that control floods. When wetlands are systematically ",
            " to make way for agriculture or urban expansion, the landscape's inherent capacity to absorb excess rainfall is significantly ",
            ". Consequently, downstream communities face a higher risk of severe inundation during storms. Conservationists emphasize that safeguarding these areas is vital not only for preserving unique biodiversity but also for ensuring the resilience of human settlements against climate variability. Restoration projects frequently focus on ",
            " native vegetation to stabilize substrates and revive local ecological networks.",
        ],
        "blanks": [
            {"options": ["trivial", "critical", "minor", "marginal"], "correct": "critical"},
            {"options": ["irrelevant", "instrumental", "passive", "indirect"], "correct": "instrumental"},
            {"options": ["removed", "eliminated", "preserved", "maintained"], "correct": "eliminated"},
            {"options": ["augmented", "diminished", "preserved", "increased"], "correct": "diminished"},
            {"options": ["reintroducing", "removing", "eliminating", "replacing"], "correct": "reintroducing"},
        ],
    },
    {
        "topic": "exercise and sleep quality",
        "text_parts": [
            "While the positive effects of physical activity on cardiovascular health are widely recognized, its impact on sleep quality is also profound. Studies indicate that moderate aerobic exercise increases the duration of deep sleep, a phase essential for the body to ",
            " and regenerate tissues. Furthermore, the rise and subsequent fall in body temperature caused by exertion can signal to the body that it is time to sleep. However, timing is critical; working out too close to bedtime may stimulate the nervous system, thereby ",
            " with the ability to fall asleep. Consequently, experts often ",
            " completing vigorous exercise at least a few hours before bed. This ensures the body has adequate time to return to a state of ",
            " necessary for a restful night.",
        ],
        "blanks": [
            {"options": ["repair", "demand", "measure", "comply"], "correct": "repair"},
            {"options": ["interfering", "assisting", "helping", "aiding"], "correct": "interfering"},
            {"options": ["advise", "allow", "encourage", "insist"], "correct": "advise"},
            {"options": ["relaxation", "excitement", "activity", "stimulation"], "correct": "relaxation"},
        ],
    },
    {
        "topic": "automation and the workforce",
        "text_parts": [
            "The integration of advanced technology into the workforce has fundamentally altered the nature of employment. Rather than simply eliminating roles, automation often ",
            " the tasks that employees must perform. As routine manual activities are taken over by algorithms and robotics, there is a growing demand for workers who possess higher-level cognitive skills. Consequently, the focus of education and training systems must ",
            " toward fostering adaptability and critical thinking. This evolution ensures that the workforce remains relevant in a rapidly changing economic landscape. Instead of fearing obsolescence, workers are encouraged to ",
            " continuous learning as a vital component of their careers. Ultimately, the successful collaboration between humans and technology depends on the ability to ",
            " these new tools effectively.",
        ],
        "blanks": [
            {"options": ["hinder", "transforms", "preserves", "eliminates"], "correct": "transforms"},
            {"options": ["stagnate", "shift", "regress", "deteriorate"], "correct": "shift"},
            {"options": ["reject", "embrace", "avoid", "dismiss"], "correct": "embrace"},
            {"options": ["leverage", "abandon", "discard", "overlook"], "correct": "leverage"},
        ],
    },
    {
        "topic": "attachment theory",
        "text_parts": [
            "Attachment theory posits that the emotional connections formed during early childhood significantly influence future behavior and interpersonal dynamics. The relationship between an infant and their primary caregiver serves as a critical ",
            " for subsequent social interactions throughout life. Securely attached children generally develop a positive self-image and operate under the assumption that they are worthy of love. Conversely, those who experience inconsistent or negligent care may struggle to ",
            " their emotions effectively, often displaying anxiety or avoidance in later relationships. These early patterns are not necessarily permanent, as significant life experiences and therapeutic interventions can ",
            " attachment styles over time. However, understanding these foundational dynamics remains crucial for psychologists attempting to ",
            " the root causes of adult relationship difficulties. By examining these initial ",
            ", individuals can gain valuable insight into their own behavioral tendencies and work towards more secure connections.",
        ],
        "blanks": [
            {"options": ["barrier", "blueprint", "dictate", "preserve"], "correct": "blueprint"},
            {"options": ["regulate", "suppress", "deplete", "enhance"], "correct": "regulate"},
            {"options": ["alter", "preserve", "dictate", "confirm"], "correct": "alter"},
            {"options": ["comprehend", "ignore", "preserve", "dispute"], "correct": "comprehend"},
            {"options": ["bonds", "conflicts", "barriers", "origins"], "correct": "bonds"},
        ],
    },
    {
        "topic": "personality plasticity",
        "text_parts": [
            "For decades, psychologists believed that personality was largely set in stone by early adulthood. Recent research, however, has ",
            " this long-held view, demonstrating that personality traits are far more plastic than previously thought. While genetic factors provide a foundation, environmental influences play a crucial role in shaping how these traits are ",
            " over time. Studies indicate that as people mature, they generally become more conscientious and emotionally stable, a trend known as the maturity principle. This suggests that personality is an adaptive system that helps individuals ",
            " the changing expectations of social roles. Ultimately, the development of character is a lifelong process that does not ",
            " after adolescence.",
        ],
        "blanks": [
            {"options": ["confirmed", "challenged", "denied", "upheld"], "correct": "challenged"},
            {"options": ["expressed", "suppressed", "established", "confirmed"], "correct": "expressed"},
            {"options": ["meet", "avoid", "ignore", "resist"], "correct": "meet"},
            {"options": ["commence", "cease", "begin", "continue"], "correct": "cease"},
        ],
    },
    {
        "topic": "history of anatomy",
        "text_parts": [
            "Andreas Vesalius is widely recognized as a pivotal figure in the history of medicine, particularly for his contributions to the study of human anatomy. Prior to his work, medical understanding was dominated by the ancient teachings of Galen, which were seldom questioned. Vesalius, however, ",
            " that accurate knowledge could only be acquired through the direct dissection of human bodies. In 1543, he published his magnum opus, which ",
            " significant errors in traditional anatomical texts that relied heavily on animal studies. By emphasizing the importance of empirical observation over blind faith in authority, Vesalius ",
            " a rigorous new approach to biological science. Although his radical methods initially faced opposition from traditionalists, they ultimately ",
            " the way for modern physiological research and surgical practice.",
        ],
        "blanks": [
            {"options": ["doubted", "insisted", "questioned", "denied"], "correct": "insisted"},
            {"options": ["exposed", "hidden", "replicated", "confirmed"], "correct": "exposed"},
            {"options": ["established", "rejected", "abolished", "questioned"], "correct": "established"},
            {"options": ["blocked", "paved", "hindered", "prevented"], "correct": "paved"},
        ],
    },
    {
        "topic": "gig economy",
        "text_parts": [
            "The rapid expansion of the gig economy has fundamentally ",
            " the nature of employment. By utilizing digital platforms, individuals can now secure short-term contracts and freelance work with unprecedented ease. While this model offers workers the ",
            " to choose their own schedules, it also presents distinct challenges regarding long-term security. The primary concern revolves around the lack of stability; gig workers often do not receive standard benefits like sick pay or pension contributions. Consequently, many find themselves in a ",
            " financial position compared to their full-time counterparts. Governments are now under pressure to ensure these independent contractors are ",
            " from exploitation without stifling the innovation that drives the sector. Ultimately, labor laws must adapt to accommodate this ",
            " economic reality.",
        ],
        "blanks": [
            {"options": ["preserved", "transformed", "stagnant", "fixed"], "correct": "transformed"},
            {"options": ["limitation", "autonomy", "authority", "control"], "correct": "autonomy"},
            {"options": ["secure", "precarious", "stable", "strong"], "correct": "precarious"},
            {"options": ["exposed", "protected", "guarded", "secure"], "correct": "protected"},
            {"options": ["stagnant", "evolving", "static", "fixed"], "correct": "evolving"},
        ],
    },
    {
        "topic": "sleep and health",
        "text_parts": [
            "Sleep is frequently undervalued in today's fast-paced society, yet it plays a critical role in maintaining both physical and mental well-being. During periods of deep sleep, the body undergoes essential biological processes that ",
            " energy levels and repair muscle tissues damaged during daily activities. Furthermore, adequate rest is vital for regulating the specific hormones that control appetite and metabolism. Consequently, a chronic lack of sleep can lead to a significant ",
            " in the risk of developing serious long-term conditions, such as obesity and heart disease. Therefore, establishing a consistent sleep schedule is a fundamental component of a healthy ",
            ". Medical experts strongly recommend that adults aim for between seven and nine hours of quality sleep each night to ensure optimal ",
            " throughout the following day.",
        ],
        "blanks": [
            {"options": ["deplete", "restore", "consume", "decline"], "correct": "restore"},
            {"options": ["drop", "increase", "decrease", "decline"], "correct": "increase"},
            {"options": ["surroundings", "lifestyle", "personality", "appearance"], "correct": "lifestyle"},
            {"options": ["performance", "appearance", "personality", "mood"], "correct": "performance"},
        ],
    },
    {
        "topic": "sleep and memory consolidation",
        "text_parts": [
            "While sleep is frequently undervalued in our fast-paced society, it plays a ",
            " role in maintaining overall well-being. During periods of deep rest, the body engages in various ",
            " processes, such as repairing tissues and strengthening the immune system. For the brain, sleep is particularly significant; it is the time when the consolidation of memory occurs, allowing the mind to process interactions and transfer information into ",
            " storage. Conversely, a chronic ",
            " of sleep can severely impair cognitive functions, reducing an individual's ability to concentrate and make sound decisions. Over time, persistent sleep deprivation is associated with an increased risk of ",
            " serious health conditions, including heart disease and diabetes.",
        ],
        "blanks": [
            {"options": ["trivial", "crucial", "minor", "marginal"], "correct": "crucial"},
            {"options": ["removing", "restorative", "damaging", "passive"], "correct": "restorative"},
            {"options": ["immediate", "long-term", "short-term", "temporary"], "correct": "long-term"},
            {"options": ["lack", "surplus", "excess", "abundance"], "correct": "lack"},
            {"options": ["curing", "developing", "preventing", "eliminating"], "correct": "developing"},
        ],
    },
]

# --------------------------------------------------------------------------
# Summarize Written Text — passages with sample one-sentence summaries
# --------------------------------------------------------------------------
SWT_PASSAGES = [
    ("climate change",
     "The increase in global temperatures has led to more frequent and severe weather events, posing a significant threat to ecosystems and human societies. One of the major impacts of climate change is the rise in sea levels, which results from the melting of polar ice caps and glaciers. Coastal areas are particularly vulnerable, as they face higher risks of flooding, storm surges, and erosion. Additionally, the warming atmosphere can hold more moisture, leading to intense and unpredictable precipitation patterns. This variability can cause both severe droughts and devastating floods, affecting agricultural productivity and water resources. The effects of climate change are widespread, influencing not only the environment but also the socio-economic stability of communities. For example, changing weather patterns can disrupt food supply chains, increase the prevalence of diseases, and force people to migrate from their homes. To mitigate these effects, countries are investing in adaptive infrastructure, developing early warning systems, and implementing policies to reduce greenhouse gas emissions.",
     "Global temperature increases are causing severe weather, sea level rise, and unpredictable precipitation, resulting in flooding, disrupted food supply chains, and forced migration, prompting nations to invest in adaptive infrastructure, early warning systems, and emissions reduction policies."),
    ("artificial intelligence and work",
     "The rise of artificial intelligence (AI) and automation is transforming industries and reshaping the job market, sparking both optimism and concern about the future of work. Proponents argue that AI has the potential to increase efficiency, reduce costs, and spur innovation across various sectors. However, the rapid adoption of AI and automation also raises significant challenges. There are widespread fears about job displacement, as machines and algorithms can perform tasks previously done by humans. A report by the World Economic Forum estimates that by 2025, automation could displace 85 million jobs globally, while also creating 97 million new roles. This transition necessitates a focus on reskilling and upskilling the workforce to prepare for new job demands. Ethical considerations and regulatory concerns also play a critical role in the AI discourse.",
     "The rise of AI and automation is transforming industries and the job market, offering increased efficiency and innovation while raising concerns about job displacement and ethical issues, necessitating a focus on reskilling the workforce and establishing regulatory frameworks to ensure responsible AI use."),
    ("remote work",
     "The rise of remote work has been one of the most significant shifts in the labor market in recent years. With advancements in technology and changing attitudes towards work-life balance, many companies have adopted flexible working arrangements. This trend was accelerated by the COVID-19 pandemic, which forced businesses worldwide to transition to remote operations almost overnight. The ability to work from anywhere has opened up new opportunities for employees and employers alike, providing greater flexibility and access to a global talent pool. However, the remote work model also presents several challenges. One of the main issues is maintaining productivity and communication among team members who are dispersed across different locations. Additionally, the blurring of boundaries between work and personal life can lead to burnout.",
     "The rise of remote work, accelerated by the COVID-19 pandemic, has transformed the labor market by offering greater flexibility and access to a global talent pool, while presenting challenges in productivity, communication, and work-life balance, leading companies to adopt hybrid models and prioritize mental health support."),
    ("CRISPR-Cas9",
     "The discovery of CRISPR-Cas9 has revolutionized the field of genetics, providing scientists with a powerful tool for editing genes with unprecedented precision. This technology allows for the targeted modification of DNA, enabling researchers to correct genetic defects, study gene function, and develop new therapies for a range of diseases. The potential applications of CRISPR are vast, including the treatment of genetic disorders such as cystic fibrosis and sickle cell anemia, as well as the enhancement of agricultural crops for better yield and disease resistance. Despite its promise, the use of CRISPR also raises ethical questions and concerns about unintended consequences. The possibility of off-target effects, where unintended parts of the genome are edited, poses risks to safety. Furthermore, the prospect of gene editing in human embryos brings up debates about the moral implications.",
     "CRISPR-Cas9 has transformed genetics by allowing precise DNA editing to correct genetic defects, study gene functions, and develop therapies, with applications in treating disorders and enhancing crops, but it also raises ethical concerns about unintended consequences and gene editing in embryos, necessitating rigorous research and oversight."),
    ("gig economy",
     "The concept of the gig economy has gained significant traction over the past decade, fundamentally altering the traditional employment landscape. Characterized by short-term contracts or freelance work, the gig economy offers flexibility and independence to workers. Companies benefit from reduced labor costs and access to a broader talent pool. However, this shift also presents challenges. Gig workers often face job insecurity, lack of benefits, and income instability. The absence of employer-provided health insurance, retirement plans, and paid leave places a significant burden on these workers. Moreover, the gig economy blurs the line between employment and entrepreneurship, complicating tax regulations and worker protections.",
     "The gig economy, marked by freelance and short-term contracts, offers flexibility and cost savings for companies but presents challenges like job insecurity, lack of benefits, and income instability for workers, leading to complex regulatory debates on worker classification and protections."),
    ("urbanization",
     "Urbanization is a global phenomenon that has transformed human societies and the environment. As more people move to cities, urban areas expand, leading to significant changes in land use and environmental impact. Urbanization offers numerous benefits, including better access to education, healthcare, and employment opportunities. Cities are often centers of innovation and cultural exchange, driving economic growth and development. However, the rapid pace of urbanization also presents several challenges. The concentration of populations in urban areas can lead to overcrowding, inadequate housing, and increased pressure on infrastructure and public services. Environmental degradation is another major concern.",
     "Urbanization, a global phenomenon transforming societies and environments, offers benefits like improved access to education and healthcare, driving economic growth, but also presents challenges such as overcrowding and environmental degradation, requiring sustainable development strategies."),
    ("urban farming",
     "Urban farming is gaining popularity as a sustainable solution to food security and environmental challenges. In densely populated cities, space is often limited, making traditional farming impractical. Urban farming initiatives utilize rooftops, vacant lots, and vertical gardens to grow fresh produce close to where people live. This approach reduces the carbon footprint associated with transporting food over long distances and provides residents with access to nutritious, locally grown food. Despite the advantages, urban farming faces several obstacles. One significant challenge is the high cost of land and property in urban areas, which can make it difficult to establish and maintain farms. Additionally, urban farmers must navigate complex regulations and zoning laws.",
     "Urban farming is emerging as a sustainable solution for food security in densely populated cities by utilizing rooftops and vertical gardens to grow fresh produce locally, reducing carbon footprint, but faces obstacles such as high land costs, regulatory hurdles, and soil contamination."),
    ("renewable energy",
     "The integration of renewable energy sources into the power grid is essential for reducing greenhouse gas emissions and combating climate change. Renewable energy technologies, such as solar, wind, and hydropower, offer a sustainable alternative to fossil fuels. These sources are abundant and produce little to no emissions during operation. The transition to renewable energy, however, presents several technical and economic challenges. One of the primary issues is the intermittent nature of renewable energy generation. Solar and wind power depend on weather conditions, which can be unpredictable and variable. This intermittency requires the development of advanced energy storage solutions and grid management technologies.",
     "Integrating renewable energy sources like solar, wind, and hydropower into the power grid is crucial for reducing emissions and combating climate change, but it faces technical challenges like energy intermittency and economic hurdles, necessitating advanced storage solutions and supportive policies."),
    ("digital divide",
     "The digital divide refers to the gap between individuals who have access to modern information and communication technologies and those who do not. This divide can exist between countries, regions, or even within communities. In the 21st century, access to the internet and digital devices is crucial for education, economic opportunities, and social participation. The lack of access to digital technologies can exacerbate existing inequalities and hinder economic development in disadvantaged areas. Efforts to bridge the digital divide include initiatives to provide affordable internet access, digital literacy programs, and investment in infrastructure.",
     "The digital divide highlights the disparity between those with access to modern technology and those without, significantly affecting education, economic opportunities, and social participation, necessitating coordinated efforts to provide affordable internet, enhance digital literacy, and invest in infrastructure."),
    ("biodiversity",
     "The importance of biodiversity cannot be overstated, as it is essential for ecosystem stability, human well-being, and economic prosperity. Biodiversity provides a wide range of ecosystem services, including pollination, water purification, and climate regulation. However, human activities such as deforestation, pollution, and climate change are leading to unprecedented rates of species extinction and habitat loss. This loss of biodiversity threatens the health of ecosystems and the services they provide. Conservation efforts are critical in protecting biodiversity. These efforts include the establishment of protected areas, habitat restoration projects, and policies aimed at reducing human impact on the environment.",
     "Biodiversity is essential for ecosystem stability, human well-being, and economic prosperity, providing critical services such as pollination and climate regulation, yet human activities are causing unprecedented species extinction and habitat loss, making conservation efforts crucial."),
    ("social media",
     "The rise of social media has transformed the way people communicate, access information, and engage with the world. Platforms like Facebook, Twitter, and Instagram have become integral parts of daily life, offering new opportunities for social interaction and information dissemination. However, the pervasive use of social media also brings challenges, including concerns about privacy, misinformation, and mental health. The spread of fake news and the manipulation of information can have serious consequences for public opinion and democratic processes. Addressing these challenges requires a multifaceted approach.",
     "The rise of social media has revolutionized communication and information access while posing challenges like privacy concerns, misinformation, and mental health issues, requiring efforts from companies, governments, and users to ensure responsible use."),
    ("e-commerce",
     "The rise of e-commerce has fundamentally changed the retail landscape, offering consumers unprecedented convenience and choice. Online shopping allows people to purchase goods from the comfort of their homes, with products delivered directly to their doorsteps. This shift has been driven by technological advancements, such as mobile devices and secure payment systems, as well as changing consumer preferences for convenience and variety. Major e-commerce platforms like Amazon and Alibaba have become dominant players, reshaping the way people shop and businesses operate. However, the growth of e-commerce has also had significant implications for traditional brick-and-mortar stores.",
     "E-commerce, driven by technology and changing consumer preferences, has revolutionized retail by providing unprecedented convenience and variety, challenging traditional stores and leading to closures, prompting many retailers to adopt omnichannel strategies and focus on sustainability."),
    ("rainforest conservation",
     "Efforts to combat climate change have led to a renewed focus on the conservation of rainforests, which play a critical role in regulating the Earth's climate. Rainforests act as carbon sinks, absorbing vast amounts of carbon dioxide and helping to mitigate the effects of global warming. In addition to their environmental benefits, rainforests are home to an incredible diversity of plant and animal species, many of which are found nowhere else on Earth. Deforestation, driven by logging, agriculture, and infrastructure development, poses a significant threat to these vital ecosystems.",
     "Efforts to combat climate change emphasize rainforest conservation due to their role in regulating Earth's climate as carbon sinks and housing unique biodiversity, with strategies like protected areas being implemented despite ongoing threats from deforestation."),
    ("global water crisis",
     "The global water crisis is one of the most pressing challenges of the 21st century. Nearly one-third of the world's population lacks access to safe drinking water, and this number is expected to rise due to factors such as population growth, climate change, and pollution. The scarcity of clean water has severe implications for health, food security, and economic development. Contaminated water sources lead to waterborne diseases, which are a major cause of mortality in developing countries. Efforts to address the water crisis include improving water management practices, investing in infrastructure, and promoting water conservation.",
     "The global water crisis, exacerbated by population growth, climate change, and pollution, threatens health, food security, and economic development, necessitating improved water management, infrastructure investment, and international cooperation to ensure equitable access to clean water for all."),
    ("climate change and agriculture",
     "Climate change is reshaping agricultural practices around the world, impacting food security and livelihoods. Rising temperatures, changing precipitation patterns, and increased frequency of extreme weather events are altering growing seasons and affecting crop yields. Farmers are being forced to adapt to these changes through the adoption of new techniques and technologies. For instance, the use of drought-resistant crop varieties and precision agriculture can help mitigate some of the adverse effects of climate change. However, adaptation alone is not enough. Reducing greenhouse gas emissions from agricultural practices is also essential to combat climate change.",
     "Climate change is significantly impacting agriculture worldwide by altering growing seasons and crop yields, necessitating the adoption of new techniques like drought-resistant crops and precision agriculture, while also requiring the reduction of greenhouse gas emissions through sustainable practices."),
]

# --------------------------------------------------------------------------
# Essay prompts
# --------------------------------------------------------------------------
ESSAY_PROMPTS = [
    ("education", "Universities should accept equal numbers of male and female students in every subject. To what extent do you agree or disagree?"),
    ("education", "Young children should spend most of their time playing rather than attending formal classes. To what extent do you agree or disagree?"),
    ("education", "In schools and universities, girls tend to choose arts subjects while boys choose science subjects. What are the reasons for this? Should governments try to change this?"),
    ("education", "Some people argue that a university education should focus on practical, vocational skills rather than academic theory. To what extent do you agree or disagree?"),
    ("education", "Studying at university is the best route to a successful career. Others believe it is better to get a job straight after school. Discuss both views and give your own opinion."),
    ("education", "Distance learning programmes are becoming more popular and may one day replace face-to-face classes. Do the advantages of this development outweigh the disadvantages?"),
    ("education", "A sense of competition in children should be encouraged. Others believe children taught to cooperate rather than compete become more useful adults. Discuss both views."),
    ("education", "Governments should spend more money on education than on solving environmental problems. To what extent do you agree or disagree?"),
    ("education", "It is more important for students to study science and technology subjects than arts and humanities. Do you agree or disagree?"),
    ("technology", "Robots and computers will eventually replace workers in all fields. Do you agree or disagree?"),
    ("technology", "Social media platforms have had a negative effect on individuals and society. To what extent do you agree or disagree?"),
    ("technology", "Technology is making communication easier in today's world, but at the expense of personal contact. Discuss the advantages and disadvantages."),
    ("technology", "The internet has transformed the way information is shared, but it has also created serious problems that did not exist before. Discuss these problems and suggest solutions."),
    ("technology", "In the modern world, it is possible to shop, work, and communicate entirely via the internet. Do the benefits of this outweigh the disadvantages?"),
    ("technology", "Artificial intelligence will soon surpass human capability in most areas of work and decision-making. To what extent do you agree or disagree?"),
    ("technology", "Technology has made life easier for most people. However, it has also caused significant environmental problems. Discuss both aspects and give your opinion."),
    ("technology", "The widespread use of smartphones has fundamentally changed the way people interact with one another. Discuss the positive and negative effects of this change."),
    ("society", "Some people believe governments should fund public services such as libraries and sports centres. Others think the private sector should fund these services. Discuss both views."),
    ("society", "The only way to reduce traffic congestion in cities is to make private car ownership very expensive. To what extent do you agree or disagree?"),
    ("society", "Unpaid community service should be a compulsory part of high school programmes. To what extent do you agree or disagree?"),
    ("society", "Governments spend large amounts of money on space exploration. Some people think this is a waste of public money. To what extent do you agree or disagree?"),
    ("society", "Some countries have introduced laws to limit working hours for employees. Why are these laws introduced? Do you think they are a good idea?"),
    ("society", "Wealthy nations should be required to share their wealth with poorer nations by providing food, education, and technology. Do you agree or disagree?"),
    ("society", "The government should control the amount of violence shown in films and on television in order to reduce violent crime in society. To what extent do you agree or disagree?"),
    ("society", "Laws that make it illegal to drive after drinking alcohol should be introduced in all countries. To what extent do you agree or disagree?"),
    ("environment", "Environmental problems such as pollution and climate change affect every country. Some people think governments should handle these problems; others believe it is the responsibility of individuals. Discuss both views."),
    ("environment", "People should reduce the amount of travel they undertake because it is one of the main causes of pollution. To what extent do you agree or disagree?"),
    ("environment", "The use of fossil fuels such as coal and oil is harming the planet. We should transition to renewable energy sources such as solar and wind power. To what extent do you agree?"),
    ("environment", "Some people believe we should reduce the amount of meat we eat because farming animals damages the environment. Others argue meat is an important part of a healthy diet. Discuss both views."),
    ("environment", "Global warming is one of the greatest threats humans face in the 21st century. What problems are associated with this? What solutions can you suggest?"),
    ("environment", "Human activity has had a largely negative impact on plants and animals around the world. Some believe this is not important as long as we protect human populations. Do you agree?"),
    ("environment", "Large corporations and multinational companies should bear the primary responsibility for addressing environmental damage. To what extent do you agree or disagree?"),
    ("media", "Advertising is an unavoidable part of modern life. Some people say it is a positive force; others say it is overwhelmingly negative. Discuss both views and include your own opinion."),
    ("media", "Advertising targeted at children is harmful and should be banned. To what extent do you agree or disagree?"),
]

# --------------------------------------------------------------------------
# Build bank items
# --------------------------------------------------------------------------
def normalize(s: str) -> str:
    return " ".join(s.split()).lower()


def build():
    bank = json.loads(BANK.read_text())
    existing_ids = {q["id"] for q in bank["questions"]}
    existing_wfd_norm = {normalize(q["answer"]) for q in bank["questions"] if q["type"] == "wfd"}
    existing_swt_norm = {normalize(q["passage"][:200]) for q in bank["questions"] if q["type"] == "swt"}
    existing_essay_norm = {normalize(q["prompt"][:120]) for q in bank["questions"] if q["type"] == "essay"}

    added = 0

    # WFD
    for i, sentence in enumerate(WFD_SENTENCES):
        if normalize(sentence) in existing_wfd_norm:
            continue
        qid = f"l-wfd-{100+i:03d}"
        if qid in existing_ids:
            continue
        bank["questions"].append({
            "id": qid,
            "section": "listening",
            "type": "wfd",
            "topic": "academic dictation",
            "audio_text": sentence,
            "answer": sentence,
            "explanation": "Type the sentence exactly. Check spelling, articles (a/an/the), singular vs plural, and verb tense. Common slips: 'their/there', 'its/it's', and silent letters.",
            "source": "alfapte/goarno (personal practice)",
        })
        added += 1

    # Reorder paragraphs
    # Store paragraphs in shuffled (display) order; answer = indices into displayed array to recover the correct order.
    import random
    rng = random.Random(42)  # deterministic for reproducibility
    for i, correct_order in enumerate(REORDER_CORRECT_ORDERS):
        qid = f"r-reorder-{100+i:03d}"
        if qid in existing_ids:
            continue
        n = len(correct_order)
        # build a shuffled mapping: displayed[j] = correct_order[perm[j]]
        perm = list(range(n))
        rng.shuffle(perm)
        displayed = [correct_order[perm[j]] for j in range(n)]
        # answer[i] = index in displayed of the i-th paragraph in correct order
        # i.e. for each correct position k, find displayed index j such that perm[j] == k
        answer = [perm.index(k) for k in range(n)]
        bank["questions"].append({
            "id": qid,
            "section": "reading",
            "type": "reorder",
            "topic": "logical flow",
            "paragraphs": displayed,
            "answer": answer,
            "explanation": "Find the topic sentence first (it stands alone without pronouns referring elsewhere). Track time markers, pronoun references (this/it/they), and connectors (however, moreover, finally) to determine sequence.",
            "trap": "Don't pick a paragraph starting with 'This', 'However', or 'Such' as the first one — these refer back to something earlier.",
            "source": "goarno (personal practice)",
        })
        added += 1

    # MCQ
    for i, q in enumerate(MCQ_QUESTIONS):
        qid = f"r-mcq-{100+i:03d}"
        if qid in existing_ids:
            continue
        bank["questions"].append({
            "id": qid,
            "section": "reading",
            "type": "mcq_single",
            "topic": q["topic"],
            "passage": q["passage"],
            "question": q["question"],
            "options": q["options"],
            "answer": q["answer"],
            "explanation": "Match each option directly to the passage. The correct option restates the passage's claim in different words; distractors either contradict the passage, exaggerate it, or add facts that aren't there.",
            "trap": "Watch for options with absolute words ('all', 'only', 'never') or that go beyond what the passage explicitly states — these are often the distractors.",
            "source": "goarno (personal practice)",
        })
        added += 1

    # FIB
    for i, q in enumerate(FIB_QUESTIONS):
        qid = f"r-fib-{100+i:03d}"
        if qid in existing_ids:
            continue
        # convert to my schema: options[][] (list of option arrays), answer[] (indices)
        options = [b["options"] for b in q["blanks"]]
        answer = []
        ok = True
        for idx, b in enumerate(q["blanks"]):
            try:
                answer.append(b["options"].index(b["correct"]))
            except ValueError:
                ok = False
                break
        if not ok or len(q["text_parts"]) != len(q["blanks"]) + 1:
            continue
        bank["questions"].append({
            "id": qid,
            "section": "reading",
            "type": "fib",
            "topic": q["topic"],
            "text_parts": q["text_parts"],
            "options": options,
            "answer": answer,
            "explanation": "Read the full sentence on each side of the blank before choosing. Match grammar (noun/verb/adjective) AND collocation (which word naturally pairs with surrounding text). The correct word usually has BOTH the right meaning AND the right grammatical form.",
            "trap": "Two options often have similar meanings but only one fits the grammar or collocation — eliminate by checking what comes right before and after the blank.",
            "source": "goarno (personal practice)",
        })
        added += 1

    # SWT
    for i, (topic, passage, sample) in enumerate(SWT_PASSAGES):
        qid = f"w-swt-{100+i:03d}"
        if qid in existing_ids:
            continue
        if normalize(passage[:200]) in existing_swt_norm:
            continue
        bank["questions"].append({
            "id": qid,
            "section": "writing",
            "type": "swt",
            "topic": topic,
            "passage": passage,
            "rubric": "ONE sentence, 5-75 words. Capture the main claim AND the key tension or caveat. Use a complex structure (although/while/despite) to show range.",
            "sample": sample,
            "grading_notes": "PTE rubric: (1) content - main idea + supporting tension 0-2 pts, (2) form - one sentence 0-1, (3) length 5-75 words 0-1, (4) grammar 0-2, (5) vocabulary 0-1. Need >=5/7 to pass.",
            "source": "goarno (personal practice)",
        })
        added += 1

    # Essays
    for i, (topic, prompt) in enumerate(ESSAY_PROMPTS):
        qid = f"w-essay-{100+i:03d}"
        if qid in existing_ids:
            continue
        if normalize(prompt[:120]) in existing_essay_norm:
            continue
        bank["questions"].append({
            "id": qid,
            "section": "writing",
            "type": "essay",
            "topic": topic,
            "prompt": prompt + " Write 200-300 words.",
            "rubric": "200-300 words. 5 paragraphs (intro+thesis / 3 body / conclusion). Address the question type (agree-disagree, discuss-both-views, advantages-disadvantages, or problem-solution) explicitly.",
            "grading_notes": "PTE essay: content 0-3, form (length+paragraphs) 0-2, development/structure 0-2, grammar 0-2, linguistic range 0-2, vocabulary range 0-2, spelling 0-2. Total 0-15. Need >=10/15 for solid pass.",
            "source": "language academy (personal practice)",
        })
        added += 1

    BANK.write_text(json.dumps(bank, indent=2, ensure_ascii=False))
    return added, len(bank["questions"])


if __name__ == "__main__":
    added, total = build()
    print(f"Added {added} questions. Bank now has {total} questions total.")
