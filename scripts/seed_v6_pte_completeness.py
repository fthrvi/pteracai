#!/usr/bin/env python3
"""Expansion v6 — PTE completeness pass.

Upgrades `describe_image` from text-prompt stub to real inline SVG visuals
(charts, maps, processes), then adds the seven PTE-Academic task types that
were missing from the bank:

  - r_fib        Reading: Fill in the Blanks (drag from shared word bank)
  - mcq_multi    Reading MCQ — Multiple Answer (negative marking)
  - lst_mcq_multi Listening MCQ — Multiple Answer (negative marking)
  - lst_fib      Listening: Fill in the Blanks (typed words in transcript)
  - lst_hcs      Highlight Correct Summary
  - lst_smw      Select Missing Word
  - lst_hiw      Highlight Incorrect Words

Idempotent: re-running replaces previously-seeded entries by id.
"""
from __future__ import annotations
import json
from pathlib import Path

BANK = Path(__file__).parent.parent / "public" / "data" / "bank.json"


# ---------------------------------------------------------------------------
# 1. Describe Image — real SVG visuals
# ---------------------------------------------------------------------------
# Each entry replaces an existing s-di-* question. We keep id/section/type/topic
# stable so saved attempts still link, but rewrite prompt, rubric, grading_notes
# and add an `image_svg` field. The renderer reads image_svg if present.

SVG_BROADBAND_LINE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 380" role="img" aria-label="Line graph of broadband adoption by country 2000-2024">
  <rect width="600" height="380" fill="#ffffff"/>
  <text x="300" y="26" text-anchor="middle" font-family="system-ui,sans-serif" font-size="15" font-weight="600" fill="#111">Households with broadband internet access, 2000–2024 (%)</text>
  <!-- axes -->
  <line x1="70" y1="320" x2="560" y2="320" stroke="#444" stroke-width="1.2"/>
  <line x1="70" y1="50" x2="70" y2="320" stroke="#444" stroke-width="1.2"/>
  <!-- y gridlines + labels -->
  <g font-family="system-ui,sans-serif" font-size="11" fill="#555">
    <line x1="70" y1="320" x2="560" y2="320" stroke="#eee"/><text x="62" y="324" text-anchor="end">0</text>
    <line x1="70" y1="266" x2="560" y2="266" stroke="#eee"/><text x="62" y="270" text-anchor="end">20</text>
    <line x1="70" y1="212" x2="560" y2="212" stroke="#eee"/><text x="62" y="216" text-anchor="end">40</text>
    <line x1="70" y1="158" x2="560" y2="158" stroke="#eee"/><text x="62" y="162" text-anchor="end">60</text>
    <line x1="70" y1="104" x2="560" y2="104" stroke="#eee"/><text x="62" y="108" text-anchor="end">80</text>
    <line x1="70" y1="50" x2="560" y2="50" stroke="#eee"/><text x="62" y="54" text-anchor="end">100</text>
  </g>
  <!-- x labels (2000, 2006, 2012, 2018, 2024) -->
  <g font-family="system-ui,sans-serif" font-size="11" fill="#555" text-anchor="middle">
    <text x="70"  y="338">2000</text>
    <text x="192" y="338">2006</text>
    <text x="315" y="338">2012</text>
    <text x="437" y="338">2018</text>
    <text x="560" y="338">2024</text>
  </g>
  <!-- South Korea (leads, rises early, saturates) -->
  <polyline fill="none" stroke="#1f77b4" stroke-width="2.2"
    points="70,304 130,250 192,160 254,90 315,68 376,60 437,55 498,52 560,50"/>
  <!-- Germany -->
  <polyline fill="none" stroke="#2ca02c" stroke-width="2.2"
    points="70,316 130,300 192,260 254,200 315,150 376,110 437,80 498,68 560,62"/>
  <!-- United States -->
  <polyline fill="none" stroke="#d62728" stroke-width="2.2"
    points="70,312 130,288 192,240 254,180 315,130 376,98 437,80 498,72 560,68"/>
  <!-- Brazil -->
  <polyline fill="none" stroke="#9467bd" stroke-width="2.2"
    points="70,319 130,316 192,300 254,265 315,220 376,170 437,130 498,108 560,95"/>
  <!-- Nigeria (lags) -->
  <polyline fill="none" stroke="#ff7f0e" stroke-width="2.2"
    points="70,320 130,319 192,316 254,308 315,290 376,260 437,225 498,195 560,170"/>
  <!-- legend -->
  <g font-family="system-ui,sans-serif" font-size="11" fill="#222">
    <rect x="430" y="56"  width="12" height="3" fill="#1f77b4"/><text x="448" y="60">South Korea</text>
    <rect x="430" y="74"  width="12" height="3" fill="#2ca02c"/><text x="448" y="78">Germany</text>
    <rect x="430" y="92"  width="12" height="3" fill="#d62728"/><text x="448" y="96">United States</text>
    <rect x="430" y="110" width="12" height="3" fill="#9467bd"/><text x="448" y="114">Brazil</text>
    <rect x="430" y="128" width="12" height="3" fill="#ff7f0e"/><text x="448" y="132">Nigeria</text>
  </g>
  <text x="20" y="185" font-family="system-ui,sans-serif" font-size="11" fill="#555" transform="rotate(-90 20 185)">% of households</text>
</svg>"""


SVG_RAINFALL_BAR = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 380" role="img" aria-label="Bar chart of monthly rainfall in four Asian cities">
  <rect width="600" height="380" fill="#ffffff"/>
  <text x="300" y="26" text-anchor="middle" font-family="system-ui,sans-serif" font-size="15" font-weight="600" fill="#111">Average monthly rainfall, four Asian cities (mm)</text>
  <line x1="80" y1="320" x2="560" y2="320" stroke="#444" stroke-width="1.2"/>
  <line x1="80" y1="50"  x2="80"  y2="320" stroke="#444" stroke-width="1.2"/>
  <g font-family="system-ui,sans-serif" font-size="11" fill="#555">
    <line x1="80" y1="320" x2="560" y2="320" stroke="#eee"/><text x="72" y="324" text-anchor="end">0</text>
    <line x1="80" y1="266" x2="560" y2="266" stroke="#eee"/><text x="72" y="270" text-anchor="end">150</text>
    <line x1="80" y1="212" x2="560" y2="212" stroke="#eee"/><text x="72" y="216" text-anchor="end">300</text>
    <line x1="80" y1="158" x2="560" y2="158" stroke="#eee"/><text x="72" y="162" text-anchor="end">450</text>
    <line x1="80" y1="104" x2="560" y2="104" stroke="#eee"/><text x="72" y="108" text-anchor="end">600</text>
    <line x1="80" y1="50"  x2="560" y2="50"  stroke="#eee"/><text x="72" y="54"  text-anchor="end">750</text>
  </g>
  <!-- Four cities × Jan / Apr / Jul / Oct (mm) -->
  <!-- Mumbai: 1, 1, 700, 60 -->
  <g fill="#1f77b4">
    <rect x="100" y="319" width="20" height="1"/>
    <rect x="220" y="319" width="20" height="1"/>
    <rect x="340" y="68"  width="20" height="252"/>
    <rect x="460" y="298" width="20" height="22"/>
  </g>
  <!-- Tokyo: 50, 130, 150, 200 -->
  <g fill="#ff7f0e">
    <rect x="122" y="302" width="20" height="18"/>
    <rect x="242" y="273" width="20" height="47"/>
    <rect x="362" y="266" width="20" height="54"/>
    <rect x="482" y="248" width="20" height="72"/>
  </g>
  <!-- Singapore: 240, 160, 160, 200 -->
  <g fill="#2ca02c">
    <rect x="144" y="234" width="20" height="86"/>
    <rect x="264" y="262" width="20" height="58"/>
    <rect x="384" y="262" width="20" height="58"/>
    <rect x="504" y="248" width="20" height="72"/>
  </g>
  <!-- Beijing: 3, 25, 175, 20 -->
  <g fill="#d62728">
    <rect x="166" y="319" width="20" height="1"/>
    <rect x="286" y="311" width="20" height="9"/>
    <rect x="406" y="257" width="20" height="63"/>
    <rect x="526" y="313" width="20" height="7"/>
  </g>
  <g font-family="system-ui,sans-serif" font-size="11" fill="#555" text-anchor="middle">
    <text x="143" y="338">January</text>
    <text x="263" y="338">April</text>
    <text x="383" y="338">July</text>
    <text x="503" y="338">October</text>
  </g>
  <g font-family="system-ui,sans-serif" font-size="11" fill="#222">
    <rect x="100" y="60" width="12" height="10" fill="#1f77b4"/><text x="118" y="69">Mumbai</text>
    <rect x="190" y="60" width="12" height="10" fill="#ff7f0e"/><text x="208" y="69">Tokyo</text>
    <rect x="270" y="60" width="12" height="10" fill="#2ca02c"/><text x="288" y="69">Singapore</text>
    <rect x="360" y="60" width="12" height="10" fill="#d62728"/><text x="378" y="69">Beijing</text>
  </g>
</svg>"""


SVG_PAPER_PROCESS = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 380" role="img" aria-label="Process diagram for paper recycling">
  <rect width="600" height="380" fill="#ffffff"/>
  <text x="300" y="26" text-anchor="middle" font-family="system-ui,sans-serif" font-size="15" font-weight="600" fill="#111">How recycled paper is made from used newspapers</text>
  <!-- five stages in a horizontal flow that wraps once -->
  <g font-family="system-ui,sans-serif" font-size="12" fill="#111" text-anchor="middle">
    <!-- Stage 1 -->
    <rect x="30" y="80" width="100" height="70" rx="6" fill="#e8f1fa" stroke="#1f77b4" stroke-width="1.5"/>
    <text x="80" y="106">1. Collection</text>
    <text x="80" y="125" font-size="10" fill="#555">newspapers</text>
    <text x="80" y="139" font-size="10" fill="#555">sorted by type</text>
    <!-- arrow -->
    <path d="M130 115 L170 115" stroke="#444" stroke-width="1.5" fill="none" marker-end="url(#a1)"/>
    <!-- Stage 2 -->
    <rect x="170" y="80" width="100" height="70" rx="6" fill="#e8f1fa" stroke="#1f77b4" stroke-width="1.5"/>
    <text x="220" y="106">2. Pulping</text>
    <text x="220" y="125" font-size="10" fill="#555">water + chemicals</text>
    <text x="220" y="139" font-size="10" fill="#555">break into fibres</text>
    <path d="M270 115 L310 115" stroke="#444" stroke-width="1.5" fill="none" marker-end="url(#a1)"/>
    <!-- Stage 3 -->
    <rect x="310" y="80" width="100" height="70" rx="6" fill="#e8f1fa" stroke="#1f77b4" stroke-width="1.5"/>
    <text x="360" y="106">3. Cleaning</text>
    <text x="360" y="125" font-size="10" fill="#555">ink, staples,</text>
    <text x="360" y="139" font-size="10" fill="#555">glue removed</text>
    <path d="M410 115 L450 115" stroke="#444" stroke-width="1.5" fill="none" marker-end="url(#a1)"/>
    <!-- Stage 4 -->
    <rect x="450" y="80" width="120" height="70" rx="6" fill="#e8f1fa" stroke="#1f77b4" stroke-width="1.5"/>
    <text x="510" y="106">4. Forming</text>
    <text x="510" y="125" font-size="10" fill="#555">slurry pressed</text>
    <text x="510" y="139" font-size="10" fill="#555">into thin sheets</text>
    <!-- corner -->
    <path d="M510 150 L510 200 L340 200" stroke="#444" stroke-width="1.5" fill="none" marker-end="url(#a1)"/>
    <!-- Stage 5 -->
    <rect x="230" y="220" width="220" height="70" rx="6" fill="#fff3e6" stroke="#ff7f0e" stroke-width="1.5"/>
    <text x="340" y="247">5. Drying &amp; finishing</text>
    <text x="340" y="266" font-size="10" fill="#555">heated rollers remove water,</text>
    <text x="340" y="280" font-size="10" fill="#555">new paper rolled and shipped</text>
  </g>
  <defs>
    <marker id="a1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
      <path d="M0 0 L10 5 L0 10 z" fill="#444"/>
    </marker>
  </defs>
  <text x="300" y="335" text-anchor="middle" font-family="system-ui,sans-serif" font-size="11" fill="#555">Each batch can be recycled 5–7 times before fibres become too short to bond.</text>
</svg>"""


SVG_DAY_PIE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 380" role="img" aria-label="Pie chart of how a typical adult spends a 24-hour day">
  <rect width="600" height="380" fill="#ffffff"/>
  <text x="300" y="26" text-anchor="middle" font-family="system-ui,sans-serif" font-size="15" font-weight="600" fill="#111">How a typical adult spends a 24-hour day</text>
  <!-- Pie centered at (220, 200) r=130 -->
  <!-- Sleep 33% (8h), Work 33% (8h), Leisure 17% (4h), Eating 8% (2h), Other 9% (2.2h) -->
  <!-- Compute arc endpoints: angles starting at top (-90 deg), clockwise -->
  <!-- Sleep: 0..118.8 deg → end at (220+130*sin(118.8), 200-130*cos(118.8)) -->
  <!-- For simplicity, use precomputed paths -->
  <g stroke="#fff" stroke-width="2">
    <!-- Sleep 8h (33.3%) blue -->
    <path d="M220,200 L220,70 A130,130 0 0,1 333.85,265 Z" fill="#4f86c6"/>
    <!-- Work 8h (33.3%) green -->
    <path d="M220,200 L333.85,265 A130,130 0 0,1 106.15,265 Z" fill="#5ca27a"/>
    <!-- Leisure 4h (16.7%) orange -->
    <path d="M220,200 L106.15,265 A130,130 0 0,1 90,200 Z" fill="#e89b4a"/>
    <!-- Eating 2h (8.3%) red -->
    <path d="M220,200 L90,200 A130,130 0 0,1 122.6,113 Z" fill="#c25656"/>
    <!-- Other 2h (8.3%) purple -->
    <path d="M220,200 L122.6,113 A130,130 0 0,1 220,70 Z" fill="#9569b8"/>
  </g>
  <!-- legend on right -->
  <g font-family="system-ui,sans-serif" font-size="12" fill="#111">
    <rect x="400" y="100" width="14" height="14" fill="#4f86c6"/><text x="422" y="112">Sleep — 8 h (33%)</text>
    <rect x="400" y="130" width="14" height="14" fill="#5ca27a"/><text x="422" y="142">Work — 8 h (33%)</text>
    <rect x="400" y="160" width="14" height="14" fill="#e89b4a"/><text x="422" y="172">Leisure — 4 h (17%)</text>
    <rect x="400" y="190" width="14" height="14" fill="#c25656"/><text x="422" y="202">Eating — 2 h (8%)</text>
    <rect x="400" y="220" width="14" height="14" fill="#9569b8"/><text x="422" y="232">Other — 2 h (8%)</text>
  </g>
  <text x="300" y="355" text-anchor="middle" font-family="system-ui,sans-serif" font-size="11" fill="#555">Source: composite of national time-use surveys, working adults aged 25–55.</text>
</svg>"""


SVG_CITY_MAP = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 380" role="img" aria-label="Side-by-side map of a city in 1950 and 2024">
  <rect width="600" height="380" fill="#ffffff"/>
  <text x="300" y="24" text-anchor="middle" font-family="system-ui,sans-serif" font-size="15" font-weight="600" fill="#111">City of Halford — urban growth, 1950 vs 2024</text>
  <!-- Two map panels -->
  <g font-family="system-ui,sans-serif" font-size="11" fill="#222">
    <!-- LEFT: 1950 -->
    <rect x="20" y="50" width="270" height="290" fill="#f6f3ec" stroke="#aaa"/>
    <text x="155" y="70" text-anchor="middle" font-weight="600">1950</text>
    <!-- river -->
    <path d="M20,200 C70,180 100,220 150,210 C200,200 230,230 290,215" fill="none" stroke="#4f86c6" stroke-width="6" opacity="0.7"/>
    <text x="100" y="195" font-size="9" fill="#1a5490">River Hal</text>
    <!-- small old town centre -->
    <rect x="115" y="155" width="50" height="40" fill="#dcd2bb" stroke="#7a6a40"/>
    <text x="140" y="178" text-anchor="middle" font-size="9">Old Town</text>
    <!-- church -->
    <polygon points="135,150 145,140 145,155" fill="#7a6a40"/>
    <!-- single railway station -->
    <circle cx="200" cy="240" r="4" fill="#222"/>
    <text x="208" y="244" font-size="9">station</text>
    <!-- two roads -->
    <line x1="20" y1="170" x2="290" y2="170" stroke="#888" stroke-width="1.5"/>
    <line x1="140" y1="50" x2="140" y2="340" stroke="#888" stroke-width="1.5"/>
    <!-- farmland labels -->
    <text x="60" y="100" font-size="9" fill="#5a8a4f">farmland</text>
    <text x="230" y="120" font-size="9" fill="#5a8a4f">farmland</text>
    <text x="240" y="290" font-size="9" fill="#5a8a4f">farmland</text>

    <!-- RIGHT: 2024 -->
    <rect x="310" y="50" width="270" height="290" fill="#f6f3ec" stroke="#aaa"/>
    <text x="445" y="70" text-anchor="middle" font-weight="600">2024</text>
    <!-- river (same) -->
    <path d="M310,200 C360,180 390,220 440,210 C490,200 520,230 580,215" fill="none" stroke="#4f86c6" stroke-width="6" opacity="0.7"/>
    <!-- expanded built-up area (light grey) -->
    <rect x="330" y="80" width="240" height="240" fill="#e8e8e8" opacity="0.7"/>
    <!-- old town preserved -->
    <rect x="405" y="155" width="50" height="40" fill="#dcd2bb" stroke="#7a6a40"/>
    <text x="430" y="178" text-anchor="middle" font-size="9">Old Town</text>
    <polygon points="425,150 435,140 435,155" fill="#7a6a40"/>
    <!-- ring road -->
    <ellipse cx="445" cy="195" rx="120" ry="115" fill="none" stroke="#222" stroke-width="2" stroke-dasharray="4 2"/>
    <text x="350" y="100" font-size="9">ring road</text>
    <!-- highway -->
    <line x1="310" y1="115" x2="580" y2="115" stroke="#d62728" stroke-width="3"/>
    <text x="525" y="110" font-size="9" fill="#d62728">M40 highway</text>
    <!-- metro line -->
    <line x1="370" y1="270" x2="540" y2="270" stroke="#2ca02c" stroke-width="2"/>
    <circle cx="385" cy="270" r="3" fill="#2ca02c"/>
    <circle cx="445" cy="270" r="3" fill="#2ca02c"/>
    <circle cx="510" cy="270" r="3" fill="#2ca02c"/>
    <text x="445" y="290" text-anchor="middle" font-size="9" fill="#2ca02c">metro line (2008)</text>
    <!-- airport icon -->
    <polygon points="540,90 555,98 540,106 543,98" fill="#222"/>
    <text x="528" y="120" font-size="9">airport</text>
    <!-- university -->
    <rect x="345" y="220" width="35" height="22" fill="#a8c4e6" stroke="#1f77b4"/>
    <text x="362" y="235" text-anchor="middle" font-size="9">univ.</text>
  </g>
  <text x="300" y="360" text-anchor="middle" font-family="system-ui,sans-serif" font-size="11" fill="#555">Shaded area = built-up zone. Compare the two panels and describe how the city expanded.</text>
</svg>"""


SVG_RENEWABLES_GROUPED = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 380" role="img" aria-label="Grouped bar chart of renewable energy mix by country">
  <rect width="600" height="380" fill="#ffffff"/>
  <text x="300" y="26" text-anchor="middle" font-family="system-ui,sans-serif" font-size="15" font-weight="600" fill="#111">Share of electricity from each renewable source, by country (%)</text>
  <line x1="80" y1="320" x2="560" y2="320" stroke="#444" stroke-width="1.2"/>
  <line x1="80" y1="50"  x2="80"  y2="320" stroke="#444" stroke-width="1.2"/>
  <g font-family="system-ui,sans-serif" font-size="11" fill="#555">
    <line x1="80" y1="320" x2="560" y2="320" stroke="#eee"/><text x="72" y="324" text-anchor="end">0</text>
    <line x1="80" y1="266" x2="560" y2="266" stroke="#eee"/><text x="72" y="270" text-anchor="end">15</text>
    <line x1="80" y1="212" x2="560" y2="212" stroke="#eee"/><text x="72" y="216" text-anchor="end">30</text>
    <line x1="80" y1="158" x2="560" y2="158" stroke="#eee"/><text x="72" y="162" text-anchor="end">45</text>
    <line x1="80" y1="104" x2="560" y2="104" stroke="#eee"/><text x="72" y="108" text-anchor="end">60</text>
    <line x1="80" y1="50"  x2="560" y2="50"  stroke="#eee"/><text x="72" y="54"  text-anchor="end">75</text>
  </g>
  <!-- 4 countries × 4 sources (solar, wind, hydro, biomass) -->
  <!-- scale: y = 320 - (val/75)*270  -->
  <!-- Germany: solar 12, wind 26, hydro 4, biomass 9 -->
  <g>
    <rect x="100" y="277" width="14" height="43" fill="#e8b341"/>
    <rect x="115" y="226" width="14" height="94" fill="#4f86c6"/>
    <rect x="130" y="306" width="14" height="14" fill="#2ca02c"/>
    <rect x="145" y="288" width="14" height="32" fill="#9569b8"/>
  </g>
  <!-- Brazil: solar 3, wind 12, hydro 56, biomass 8 -->
  <g>
    <rect x="220" y="309" width="14" height="11" fill="#e8b341"/>
    <rect x="235" y="277" width="14" height="43" fill="#4f86c6"/>
    <rect x="250" y="118" width="14" height="202" fill="#2ca02c"/>
    <rect x="265" y="291" width="14" height="29" fill="#9569b8"/>
  </g>
  <!-- China: solar 8, wind 11, hydro 15, biomass 2 -->
  <g>
    <rect x="340" y="291" width="14" height="29" fill="#e8b341"/>
    <rect x="355" y="280" width="14" height="40" fill="#4f86c6"/>
    <rect x="370" y="266" width="14" height="54" fill="#2ca02c"/>
    <rect x="385" y="313" width="14" height="7" fill="#9569b8"/>
  </g>
  <!-- USA: solar 6, wind 11, hydro 6, biomass 1 -->
  <g>
    <rect x="460" y="298" width="14" height="22" fill="#e8b341"/>
    <rect x="475" y="280" width="14" height="40" fill="#4f86c6"/>
    <rect x="490" y="298" width="14" height="22" fill="#2ca02c"/>
    <rect x="505" y="316" width="14" height="4" fill="#9569b8"/>
  </g>
  <g font-family="system-ui,sans-serif" font-size="11" fill="#555" text-anchor="middle">
    <text x="130" y="338">Germany</text>
    <text x="250" y="338">Brazil</text>
    <text x="370" y="338">China</text>
    <text x="490" y="338">USA</text>
  </g>
  <g font-family="system-ui,sans-serif" font-size="11" fill="#222">
    <rect x="100" y="58" width="12" height="10" fill="#e8b341"/><text x="118" y="68">Solar</text>
    <rect x="170" y="58" width="12" height="10" fill="#4f86c6"/><text x="188" y="68">Wind</text>
    <rect x="240" y="58" width="12" height="10" fill="#2ca02c"/><text x="258" y="68">Hydro</text>
    <rect x="310" y="58" width="12" height="10" fill="#9569b8"/><text x="328" y="68">Biomass</text>
  </g>
</svg>"""


DESCRIBE_IMAGE_UPDATES = [
    {
        "id": "s-di-100",
        "topic": "line graph",
        "image_svg": SVG_BROADBAND_LINE,
        "prompt": "Look at the line graph and describe what you see in 25 seconds. Cover the overall trend, the country that leads, and one striking contrast between countries.",
        "rubric": "25-second monologue. Template: 1 sentence introducing what the graph shows; 1-2 sentences naming the highest and lowest trajectories; 1 specific year-to-year change worth highlighting; 1 closing line on the overall pattern.",
        "grading_notes": "Content credit requires naming (a) at least two countries by name from the legend, (b) at least one specific number or year, (c) the overall direction of the trend. Penalise vague filler ('many things are happening', 'it goes up and down') with no specific data.",
    },
    {
        "id": "s-di-101",
        "topic": "bar chart",
        "image_svg": SVG_RAINFALL_BAR,
        "prompt": "Look at the bar chart and describe it in 25 seconds. Identify the wettest and driest city, and one striking seasonal pattern.",
        "rubric": "25-second monologue. Template: 1 sentence on what the chart shows; 1 sentence picking out the wettest single bar; 1 sentence on the driest city overall; 1 closing line on the dominant seasonal pattern (monsoon vs. even-distribution).",
        "grading_notes": "Content credit requires naming at least two of the four cities, citing at least one numeric rainfall value or comparison ('roughly five times higher'), and noting that Mumbai's July peak dominates the chart. Penalise 'all the cities get rain in summer' as too vague.",
    },
    {
        "id": "s-di-102",
        "topic": "process diagram",
        "image_svg": SVG_PAPER_PROCESS,
        "prompt": "Look at the process diagram and describe the five stages of paper recycling in your own words. Speak for 25 seconds.",
        "rubric": "25-second monologue. Template: 1-sentence intro identifying it as a process diagram; one sentence per major stage using sequencers ('first', 'next', 'then', 'finally'); 1 closing line on the outcome.",
        "grading_notes": "Content credit requires naming at least four of the five stages and using at least two distinct sequencer words. Penalise jumping straight to 'and then paper comes out' without naming intermediate steps.",
    },
    {
        "id": "s-di-103",
        "topic": "pie chart",
        "image_svg": SVG_DAY_PIE,
        "prompt": "Look at the pie chart and describe how a typical adult spends a 24-hour day. Speak for 25 seconds. Highlight the largest and smallest slices.",
        "rubric": "25-second monologue. Template: 1-sentence intro; 1 sentence on the two largest slices (sleep and work are tied at 33% each); 1 sentence on the smallest slices; 1 closing comparison or observation.",
        "grading_notes": "Content credit requires naming sleep and work as the tied largest at roughly one-third each, naming eating or 'other' as the smallest, and citing at least one specific percentage or hour figure. Penalise unsupported claims ('most people spend most of their day on social media').",
    },
    {
        "id": "s-di-104",
        "topic": "map",
        "image_svg": SVG_CITY_MAP,
        "prompt": "Compare the two maps of Halford (1950 vs. 2024) and describe how the city has changed. Speak for 25 seconds.",
        "rubric": "25-second monologue. Template: 1-sentence intro framing it as a before/after comparison; 1 sentence on what has been preserved (Old Town, the river); 1 sentence on new infrastructure (ring road, highway, metro, airport, university); 1 closing line on overall expansion.",
        "grading_notes": "Content credit requires naming at least three new features added by 2024 and at least one element that has been preserved. Penalise descriptions that only list features without contrasting the two panels.",
    },
    {
        "id": "s-di-105",
        "topic": "comparative chart",
        "image_svg": SVG_RENEWABLES_GROUPED,
        "prompt": "Look at the grouped bar chart and describe the renewable energy mix across four countries. Speak for 25 seconds.",
        "rubric": "25-second monologue. Template: 1-sentence intro; 1 sentence picking the country that leads in any specific source (Brazil in hydro is the most striking); 1 sentence on Germany's wind lead; 1 closing line summarising the cross-country pattern.",
        "grading_notes": "Content credit requires naming Brazil's hydro dominance (the tallest single bar on the chart), naming at least one other country–source pairing with a number, and contrasting two countries explicitly. Penalise descriptions that just list percentages without ranking or contrast.",
    },
]


# ---------------------------------------------------------------------------
# 2. New PTE question types
# ---------------------------------------------------------------------------

# 2a. Reading FIB — drag-and-drop with shared word bank
R_FIB = [
    {
        "id": "r-rfib-001",
        "section": "reading",
        "type": "r_fib",
        "topic": "academic vocabulary",
        "text_parts": [
            "Recent research into early childhood development has ",
            "",
            " a long-standing belief that emotional regulation is largely innate. The new findings instead ",
            "",
            " a strong role for environmental factors, particularly the responsiveness of primary caregivers during the first two years of life. Children whose distress signals are met with consistent, ",
            "",
            " attention develop measurably stronger self-soothing skills by age four.",
        ],
        "word_bank": ["challenged", "confirmed", "suggest", "ignore", "attuned", "absent", "distracted", "predicted"],
        "answer": [0, 2, 4],
        "explanation": "(1) 'challenged' fits the setup ('upended a long-standing belief'); 'confirmed' would contradict 'long-standing belief'. (2) 'suggest a strong role' is the standard collocation for new findings — 'ignore' makes no sense, 'predicted' would imply forecasting rather than describing the present finding. (3) 'attuned attention' is the academic register; 'absent' and 'distracted' would contradict 'consistent, responsive caregivers'.",
        "trap": "Test-takers reach for 'confirmed' in blank 1 because it's the most common verb. Read the next clause — 'instead' signals a contrast, which forces 'challenged'.",
    },
    {
        "id": "r-rfib-002",
        "section": "reading",
        "type": "r_fib",
        "topic": "academic vocabulary",
        "text_parts": [
            "The traditional view of the Mediterranean as a single ",
            "",
            " region masks substantial internal variation. Rainfall patterns in coastal Spain differ ",
            "",
            " from those of the eastern Mediterranean, and these differences are ",
            "",
            " by changes in elevation, distance from the coast, and prevailing wind directions.",
        ],
        "word_bank": ["climatic", "political", "markedly", "slightly", "amplified", "eliminated", "imagined", "fixed"],
        "answer": [0, 2, 4],
        "explanation": "(1) 'climatic' — the sentence is about rainfall and climate; 'political' is irrelevant. (2) 'markedly' — 'differ markedly' is the academic collocation, and 'slightly' would weaken the writer's argument that the region is internally varied. (3) 'amplified' — terrain features make differences bigger, not smaller; 'eliminated' would contradict the paragraph's thesis.",
        "trap": "Blank 2: 'slightly' is grammatical but semantically wrong — it would undermine the argument the paragraph is building. Always check whether your word reinforces or contradicts the writer's overall claim.",
    },
    {
        "id": "r-rfib-003",
        "section": "reading",
        "type": "r_fib",
        "topic": "academic vocabulary",
        "text_parts": [
            "Modern algorithmic trading systems can execute orders in microseconds, but speed alone does not ",
            "",
            " profitability. The most successful funds invest heavily in research that ",
            "",
            " subtle, persistent patterns in market data — patterns too small or too fleeting for human traders to ",
            "",
            ".",
        ],
        "word_bank": ["guarantee", "explain", "identifies", "creates", "exploit", "ignore", "remember", "obstruct"],
        "answer": [0, 2, 4],
        "explanation": "(1) 'guarantee' — the contrast 'but ... not ___ profitability' calls for 'guarantee'; 'explain' is grammatical but doesn't fit the argument. (2) 'identifies' — research uncovers patterns, it doesn't 'create' them in this context. (3) 'exploit' — the standard verb pair with 'patterns in market data' is 'identify and exploit'.",
        "trap": "Blank 2: 'creates' is tempting because algorithms 'create' things. Re-read: research describes pre-existing patterns; it doesn't fabricate them.",
    },
    {
        "id": "r-rfib-004",
        "section": "reading",
        "type": "r_fib",
        "topic": "academic vocabulary",
        "text_parts": [
            "Historians once dismissed oral traditions as ",
            "",
            " sources, preferring written records that they considered more ",
            "",
            ". Recent scholarship has ",
            "",
            " this hierarchy, demonstrating that oral histories can preserve fine-grained detail across many generations when transmission is structured by formal mnemonic conventions.",
        ],
        "word_bank": ["unreliable", "essential", "trustworthy", "incomplete", "overturned", "endorsed", "ignored", "documented"],
        "answer": [0, 2, 4],
        "explanation": "(1) 'unreliable' — 'dismissed as ___ sources' calls for a negative descriptor; 'essential' would reverse the meaning. (2) 'trustworthy' — they preferred written records they considered MORE ___; 'incomplete' makes no sense. (3) 'overturned' — 'recent scholarship has' + past participle that contradicts the older view; 'endorsed' would mean agreeing with the old hierarchy.",
        "trap": "Blank 3: 'endorsed' is grammatical but takes the wrong side of the argument. Always trace whose view the sentence is reporting.",
    },
]

# 2b. Reading MCQ Multiple Answer (negative marking)
MCQ_MULTI = [
    {
        "id": "r-mcm-001",
        "section": "reading",
        "type": "mcq_multi",
        "topic": "main idea + supporting detail",
        "passage": "Cities that have invested in dedicated cycling infrastructure — protected lanes, bike-priority signals, and secure parking — see cycling rates roughly triple within a decade. The pattern holds across cities as different as Copenhagen, Bogotá, and Portland. What's notable is that infrastructure alone is not enough: cities that built lanes but did not also re-time intersection signals to favour cyclists saw only modest gains. Where serious uptake has happened, three conditions co-occur: continuous, protected lanes; signal timing that gives cyclists a head start; and visible enforcement against parking in bike lanes. Cities that have tried to attract cyclists through information campaigns alone, without changing the physical street, have seen no measurable change.",
        "question": "According to the passage, which TWO of the following are necessary for cycling rates to rise substantially? (Select TWO)",
        "options": [
            "Continuous protected cycling lanes.",
            "Public information and education campaigns.",
            "Signal timing that favours cyclists at intersections.",
            "Higher taxes on private cars.",
            "Mandatory cycling lessons in schools.",
        ],
        "answer": [0, 2],
        "explanation": "The passage explicitly names three co-occurring conditions: protected lanes (A), signal timing (C), and enforcement. B is contradicted ('information campaigns alone ... no measurable change'). D and E are not mentioned.",
        "trap": "B looks plausible because campaigns 'should' help — but the passage explicitly says they don't on their own. With negative marking, only pick options the passage clearly supports.",
    },
    {
        "id": "r-mcm-002",
        "section": "reading",
        "type": "mcq_multi",
        "topic": "scientific argument",
        "passage": "Coral reef bleaching is often portrayed as an unambiguous death sentence, but reefs can recover from a single bleaching event if water temperatures fall within a few weeks. The danger now is the rising frequency of consecutive bleaching events: corals need eight to twelve years between major heat stresses to rebuild their algal partners and skeletal structure. When bleaching happens every three or four years — as is increasingly common — recovery is incomplete and cumulative damage accelerates. Importantly, the species composition of recovering reefs has begun to shift, with fast-growing but structurally fragile branching corals replacing the slower-growing massive corals that once dominated. The new reefs are real, but they support a markedly different ecosystem.",
        "question": "Which TWO claims does the passage support? (Select TWO)",
        "options": [
            "A single bleaching event is always fatal to a coral reef.",
            "Reefs need roughly a decade between major heat stresses to fully recover.",
            "Frequent bleaching is altering the species mix of reefs.",
            "Branching corals are more resilient than massive corals to heat stress.",
            "Coral bleaching is a problem only in tropical Pacific reefs.",
        ],
        "answer": [1, 2],
        "explanation": "B paraphrases 'eight to twelve years between major heat stresses'. C paraphrases 'species composition ... has begun to shift'. A is contradicted by the opening ('can recover from a single bleaching event'). D is the opposite of the passage ('branching corals' are described as 'structurally fragile'). E is not in the passage at all.",
        "trap": "D inverts the actual claim — branching corals replace massive corals, but the passage doesn't say they're more resilient, just faster-growing. With negative marking, do NOT guess on inversions.",
    },
    {
        "id": "r-mcm-003",
        "section": "reading",
        "type": "mcq_multi",
        "topic": "policy + evidence",
        "passage": "Universal pre-kindergarten programs have been promoted as a way to close achievement gaps before they take root. The evidence is more nuanced than advocates claim. High-quality programs with small class sizes, well-trained teachers, and a structured curriculum produce durable gains in reading and self-regulation through at least age 14. Programs that look the same on paper but operate with high staff turnover or rely heavily on under-qualified aides show initial gains that fade by third grade. The factor that most consistently predicts long-term success is not whether a program exists, but whether teachers are paid competitively enough to stay in their roles for at least five years.",
        "question": "Which TWO statements are supported by the passage? (Select TWO)",
        "options": [
            "All pre-K programs produce equal long-term gains.",
            "Teacher retention is a key predictor of program effectiveness.",
            "Programs with high staff turnover often see early gains disappear by third grade.",
            "Pre-K programs eliminate achievement gaps entirely.",
            "Small class sizes alone are sufficient to guarantee long-term gains.",
        ],
        "answer": [1, 2],
        "explanation": "B paraphrases the final sentence directly. C paraphrases 'high staff turnover ... initial gains that fade by third grade'. A is contradicted (programs differ). D overstates ('close gaps' ≠ 'eliminate gaps'). E is not stated — small class size is one factor among several.",
        "trap": "D is the absolutist version of an actual claim. 'Close achievement gaps' was the advocates' goal — the passage doesn't endorse 'eliminate'. Avoid extremity words.",
    },
]

# 2c. Listening MCQ Multiple Answer
LST_MCQ_MULTI = [
    {
        "id": "l-mcm-001",
        "section": "listening",
        "type": "lst_mcq_multi",
        "topic": "academic lecture",
        "audio_text": "Today I want to focus on what makes peer review work — and what makes it fail. The strengths of peer review are real: it filters out obvious methodological errors, it catches missing citations and overstated claims, and it gives editors a structured signal about which papers deserve scarce journal space. But the system has well-documented weaknesses. Reviewers tend to favour work that confirms their priors, novel or interdisciplinary work gets lower scores than incremental work in established traditions, and the time investment is unrewarded — most reviewers report doing it from a sense of professional duty rather than expectation of any return. Reform proposals tend to cluster around three ideas: paying reviewers, opening reviews to public scrutiny after publication, and using pre-registration to reduce the temptation to evaluate results rather than methods.",
        "question": "Which TWO of the following does the lecturer identify as WEAKNESSES of peer review? (Select TWO)",
        "options": [
            "It filters out methodological errors.",
            "Reviewers tend to favour work that confirms their existing views.",
            "Reviewers receive substantial financial rewards for the work.",
            "Novel or interdisciplinary work gets lower scores than incremental work.",
            "Reviewers always reach the same conclusions about a paper.",
        ],
        "answer": [1, 3],
        "explanation": "B and D paraphrase 'favour work that confirms their priors' and 'novel or interdisciplinary work gets lower scores'. A is named as a STRENGTH, not a weakness. C contradicts 'the time investment is unrewarded'. E is not in the lecture.",
        "trap": "A is in the lecture but on the wrong side — it's listed as a strength. Don't pick options just because the words appeared in the audio.",
    },
    {
        "id": "l-mcm-002",
        "section": "listening",
        "type": "lst_mcq_multi",
        "topic": "academic lecture",
        "audio_text": "Memory researchers now distinguish three broad consolidation pathways. The first is synaptic consolidation, which happens within minutes to hours after learning and depends on protein synthesis at specific synapses. The second is systems consolidation, which unfolds over weeks to years and gradually transfers memories from the hippocampus to neocortical storage. The third — and most recently characterised — is reconsolidation, the surprising finding that retrieved memories briefly become labile again and can be modified before being restored. Reconsolidation has opened a clinical window: post-traumatic memories can sometimes be weakened by retrieving them under specific pharmacological conditions, though the technique remains experimental.",
        "question": "Which TWO statements does the lecturer make about reconsolidation? (Select TWO)",
        "options": [
            "It is the longest of the three consolidation processes.",
            "Retrieved memories briefly become modifiable before being restored.",
            "It has potential clinical applications for traumatic memories.",
            "It replaces systems consolidation entirely.",
            "It requires protein synthesis at every synapse.",
        ],
        "answer": [1, 2],
        "explanation": "B paraphrases 'retrieved memories briefly become labile again and can be modified'. C paraphrases 'opened a clinical window ... post-traumatic memories can sometimes be weakened'. A is wrong — systems consolidation is described as the longest. D is not stated; the three processes coexist. E is described for synaptic consolidation, not reconsolidation.",
        "trap": "E mixes details from a different pathway. The lecturer mentions protein synthesis only in connection with synaptic consolidation. Track which detail attaches to which concept.",
    },
    {
        "id": "l-mcm-003",
        "section": "listening",
        "type": "lst_mcq_multi",
        "topic": "academic lecture",
        "audio_text": "Geothermal energy is often described as a promising baseload renewable, but its real-world deployment has been uneven. The clearest successes are in places with shallow, naturally permeable hot rock: Iceland, parts of New Zealand, and the western United States. Most of the planet doesn't have that geology. Enhanced geothermal systems try to engineer permeability by fracturing deeper rock, but the technique has been linked to small induced earthquakes near several pilot sites. Cost is the other constraint: drilling deep enough to reach useful temperatures often runs above a hundred million dollars per project, and that cost has not fallen the way solar and wind costs have over the last fifteen years.",
        "question": "Which TWO challenges to wider geothermal deployment does the lecturer mention? (Select TWO)",
        "options": [
            "Most regions lack the right geology near the surface.",
            "Geothermal plants emit large amounts of carbon dioxide.",
            "Enhanced systems have been linked to induced seismic activity.",
            "The technology requires year-round sunlight.",
            "Most countries have banned the use of geothermal energy.",
        ],
        "answer": [0, 2],
        "explanation": "A paraphrases 'Most of the planet doesn't have that geology'. C paraphrases 'linked to small induced earthquakes'. B is not mentioned (the lecture calls it renewable). D is irrelevant to geothermal. E is not stated.",
        "trap": "B taps a general assumption that all energy sources emit CO2. The lecturer specifically frames geothermal as a clean baseload renewable. Stick to what was said.",
    },
]

# 2d. Listening FIB — typed words in transcript
LST_FIB = [
    {
        "id": "l-lfib-001",
        "section": "listening",
        "type": "lst_fib",
        "topic": "academic lecture",
        "audio_text": "The study of bird migration has been revolutionised by miniature tracking devices weighing less than a gram. These transmitters can be fitted to birds as small as warblers without affecting flight performance, and they reveal that many species follow remarkably precise routes year after year. Some songbirds navigate using a combination of star patterns at night and the Earth's magnetic field during the day, a redundancy that helps them stay on course even when one cue is obscured by weather.",
        "text_parts": [
            "Miniature tracking devices that weigh less than a ",
            "",
            " have revealed that many bird species follow remarkably precise routes year after ",
            "",
            ". Some songbirds use both star patterns at night and the Earth's ",
            "",
            " field during the day, a redundancy that protects them from weather that obscures one cue.",
        ],
        "answer": ["gram", "year", "magnetic"],
        "explanation": "Each blank is a single content word lifted directly from the audio. The grammar of the surrounding sentence narrows the options: 'less than a ___' demands a unit of weight; 'year after ___' is a fixed phrase; 'Earth's ___ field' is a fixed compound noun.",
        "trap": "Listeners often type the first plausible word they catch ('ounce' or 'gram' for blank 1). Wait for the actual word in the audio — the test grades exact matches, not synonyms.",
    },
    {
        "id": "l-lfib-002",
        "section": "listening",
        "type": "lst_fib",
        "topic": "academic lecture",
        "audio_text": "Soil scientists have started to map the underground network of fungal threads that connect tree roots across forest floors. These threads — collectively called the mycorrhizal network — allow trees to share nutrients, particularly nitrogen and phosphorus, and to send chemical warning signals when pests attack a neighbour. Older, larger trees often function as hubs in these networks, supporting younger saplings during their establishment years.",
        "text_parts": [
            "The underground network of fungal threads connecting tree roots is collectively called the ",
            "",
            " network. It allows trees to share ",
            "",
            " — particularly nitrogen and phosphorus — and to send chemical warning ",
            "",
            " when pests attack a neighbour.",
        ],
        "answer": ["mycorrhizal", "nutrients", "signals"],
        "explanation": "Three content words from the lecture. 'Mycorrhizal' is the technical term used; 'fungal' would be a paraphrase but won't be accepted because the audio uses 'mycorrhizal'. 'Nutrients' is followed in the audio by an em-dash listing examples. 'Signals' completes the fixed pairing 'chemical warning signals'.",
        "trap": "Don't try to spell unfamiliar scientific words by ear. If the audio uses 'mycorrhizal', it's worth replaying once to nail the spelling, since this question awards no partial credit on a single typo.",
    },
    {
        "id": "l-lfib-003",
        "section": "listening",
        "type": "lst_fib",
        "topic": "academic lecture",
        "audio_text": "When we talk about traffic congestion, the natural reaction is to assume that adding road capacity will reduce delays. Decades of evidence point the other way. New lanes attract new drivers in a phenomenon economists call induced demand: travel that was previously discouraged by congestion now happens, and within a few years the new road is as crowded as the old one. The lesson is counter-intuitive — when congestion is the constraint, building more road space often does not solve the problem.",
        "text_parts": [
            "Adding road capacity tends to attract new drivers in a phenomenon economists call ",
            "",
            " demand. Within a few ",
            "",
            ", the new road is typically as crowded as the old one, which is why building more road space often does not ",
            "",
            " congestion.",
        ],
        "answer": ["induced", "years", "solve"],
        "explanation": "Three content words from the lecture. 'Induced demand' is the technical term defined explicitly. 'Years' (not 'months') is the timescale used. 'Solve' is the verb in the closing sentence; 'reduce' is plausible but the audio specifically says 'does not solve'.",
        "trap": "Blank 3 invites guesses like 'reduce' or 'eliminate'. The lecturer used 'solve' — write what you heard, not what feels natural.",
    },
]

# 2e. Highlight Correct Summary
LST_HCS = [
    {
        "id": "l-hcs-001",
        "section": "listening",
        "type": "lst_hcs",
        "topic": "academic lecture",
        "audio_text": "Researchers in linguistics have long debated whether the structure of a language shapes the way its speakers think. The strong form of this hypothesis — that language strictly determines cognition — has been broadly rejected. But weaker versions are gathering empirical support. Speakers of languages with grammatical gender categorise objects differently from speakers of languages without it. Speakers of languages that use absolute directions, like north and south, rather than relative ones, like left and right, develop remarkable spatial awareness that persists even in unfamiliar environments. These effects are small, but they are real, and they have begun to reshape how cognitive scientists think about the interaction between thought and language.",
        "question": "Which summary best captures the main point of the lecture?",
        "options": [
            "Linguists have proven that language entirely determines the way speakers think, and the strong form of this hypothesis is now accepted across the field.",
            "While the strong form of the language-shapes-thought hypothesis has been rejected, weaker versions are now supported by small but real effects involving grammatical gender and spatial-direction conventions.",
            "Languages with grammatical gender make speakers think exactly the same as speakers of languages without it, and direction systems have no measurable effect on cognition.",
            "Cognitive scientists have given up studying the interaction between thought and language because the experimental evidence is too weak to be useful.",
        ],
        "answer": 1,
        "explanation": "Option B preserves the lecturer's nuanced position: strong hypothesis rejected, weaker versions supported, effects small but real. A inverts the actual conclusion. C contradicts the lecture's evidence. D is the opposite of the closing line about reshaping cognitive science.",
        "trap": "A is dangerous because it uses the same vocabulary as the lecture ('strong form', 'language determines thought') but takes the opposite side. Read for direction of argument, not keyword overlap.",
    },
    {
        "id": "l-hcs-002",
        "section": "listening",
        "type": "lst_hcs",
        "topic": "academic lecture",
        "audio_text": "When public health officials talk about vaccine hesitancy, the temptation is to frame it as a problem of misinformation, fixable through better education campaigns. The evidence suggests this framing is incomplete. Surveys consistently find that vaccine-hesitant parents are not less informed about vaccines — many have read extensively on the topic. What distinguishes them is lower baseline trust in the institutions delivering the message: government health agencies, pharmaceutical companies, and sometimes physicians themselves. Interventions that focus on information delivery without first rebuilding institutional trust tend to backfire, producing more entrenched hesitancy rather than less. Effective programs invest first in trusted local messengers — community doctors, pharmacists, religious leaders — who can carry the same scientific content with credibility the institution itself cannot supply.",
        "question": "Which summary best captures the main point of the lecture?",
        "options": [
            "Vaccine hesitancy is mainly a problem of poor information, and the standard solution of public education campaigns has been highly successful.",
            "Vaccine-hesitant parents are uniformly less educated and have read less about vaccines than parents who vaccinate readily.",
            "Vaccine hesitancy is driven less by lack of information than by low trust in institutional messengers, so effective interventions rely on trusted local figures rather than information delivery alone.",
            "Effective public health campaigns target individual fears through one-on-one therapy, while institutional messaging plays only a minor role.",
        ],
        "answer": 2,
        "explanation": "C captures the lecture's core claim: trust matters more than information, and local messengers carry credibility institutions cannot. A reverses the lecture's framing. B contradicts ('not less informed'). D is not in the lecture at all.",
        "trap": "A reuses the lecture's framing ('information', 'public education') but takes the position the lecturer is arguing AGAINST. Anchor on the conclusion, not the surface vocabulary.",
    },
    {
        "id": "l-hcs-003",
        "section": "listening",
        "type": "lst_hcs",
        "topic": "academic lecture",
        "audio_text": "The history of antibiotic resistance is often told as a story of bacteria evolving to defeat human medicine. That framing is misleading. Resistance genes existed in the soil microbiome long before penicillin was discovered — antibiotic compounds are produced naturally by competing microbes, and bacteria have been evolving counter-measures for millions of years. What human medicine did was unwittingly accelerate selection. The widespread use of antibiotics in agriculture and the over-prescription of antibiotics for viral infections created conditions where pre-existing resistance genes became overwhelmingly advantageous, spread rapidly through bacterial populations, and reached clinical settings. The implication is that 'discovering new antibiotics faster' is a partial fix at best — without changing how existing antibiotics are used, the same arms race will repeat.",
        "question": "Which summary best captures the main point of the lecture?",
        "options": [
            "Antibiotic resistance is a recent invention by bacteria, and discovering new antibiotics is the complete solution to the problem.",
            "Resistance genes existed in nature long before human medicine; modern misuse of antibiotics accelerated their spread, so simply inventing new drugs won't solve the underlying problem.",
            "Antibiotic-resistant bacteria are a myth perpetuated by pharmaceutical companies to sell new drugs.",
            "Agricultural use of antibiotics is the sole cause of resistance, and human medical use plays no role.",
        ],
        "answer": 1,
        "explanation": "B captures both halves of the lecturer's argument: pre-existing resistance + human acceleration + 'new drugs alone won't fix it'. A is the framing the lecturer rejects. C is not a position in the lecture. D singles out one cause while the lecture names multiple.",
        "trap": "D picks out one fact from the audio (agricultural use) and inflates it into a sole cause. Summaries fail not only by contradicting evidence but by over-attributing.",
    },
]

# 2f. Select Missing Word
LST_SMW = [
    {
        "id": "l-smw-001",
        "section": "listening",
        "type": "lst_smw",
        "topic": "academic lecture",
        # audio_text contains what TTS reads. We deliberately cut off before the final word.
        "audio_text": "When economists first started studying happiness as an outcome variable, the surprising finding was how little additional income increased self-reported well-being once a household had moved out of poverty. Across high-income countries, the gap between earning fifty thousand and earning a hundred thousand dollars per year produces only a modest increase in reported happiness. The dominant predictor at those income levels is not money but the strength of close personal",
        "question": "Which word or phrase best completes the recording?",
        "options": ["relationships", "education", "investments", "ambitions"],
        "answer": 0,
        "explanation": "The lecture explicitly contrasts money with the predictor of happiness at high income levels and frames it around 'close personal ___'. The standard pairing is 'close personal relationships'.",
        "trap": "All four options fit grammatically ('close personal investments' is grammatical too), but only 'relationships' fits the well-known finding from happiness economics that the lecture is leading to.",
    },
    {
        "id": "l-smw-002",
        "section": "listening",
        "type": "lst_smw",
        "topic": "academic lecture",
        "audio_text": "Modern cryptography rests on two foundations. The first is the use of mathematical problems that are easy to compute in one direction but extremely hard to reverse — multiplying two large prime numbers, for example, is fast, but factoring the result is computationally expensive. The second foundation is the careful management of secret keys: a perfect mathematical scheme is worthless if the keys can be intercepted or guessed. The whole field, in other words, depends as much on key management as it does on",
        "question": "Which word or phrase best completes the recording?",
        "options": ["budgets", "mathematics", "advertising", "compliance"],
        "answer": 1,
        "explanation": "The lecture's argument structure is 'as much on X as on Y' where Y is the other foundation discussed. The first foundation was hard mathematical problems, so 'mathematics' is the only option that closes the parallel.",
        "trap": "'Compliance' sounds professional and security-adjacent, but the lecture never raised compliance as a foundation. Track the actual structure of the argument, not vibes-related distractors.",
    },
    {
        "id": "l-smw-003",
        "section": "listening",
        "type": "lst_smw",
        "topic": "academic lecture",
        "audio_text": "Field biologists studying coral reefs have noticed that the recovery of bleached reefs depends heavily on the surrounding ocean conditions. Reefs near coastlines with healthy mangrove forests recover more reliably than reefs adjacent to coastlines where mangroves have been cleared. Mangroves filter sediment from runoff, stabilise water temperature in lagoons, and serve as nurseries for juvenile reef fish. In short, the fate of a coral reef cannot be understood without also understanding the health of its neighbouring",
        "question": "Which word or phrase best completes the recording?",
        "options": ["industries", "mangroves", "predators", "tourists"],
        "answer": 1,
        "explanation": "The entire passage is a setup for the final word: mangroves are named four times and presented as the relevant neighbouring ecosystem. 'Predators' and 'tourists' are not discussed; 'industries' could fit loosely but the lecture is not about industry.",
        "trap": "Test-takers who tune out for the buildup may grab any noun. The Select Missing Word task often rewards listeners who track what the lecture has been building toward.",
    },
]

# 2g. Highlight Incorrect Words
LST_HIW = [
    {
        "id": "l-hiw-001",
        "section": "listening",
        "type": "lst_hiw",
        "topic": "academic lecture",
        # audio_text is what TTS reads aloud (the correct version)
        "audio_text": "The Antarctic ice sheet has been losing mass at an accelerating rate since the early 1990s, with most of the loss concentrated in West Antarctica where warming ocean currents are eroding the floating ice shelves that buttress inland glaciers.",
        # transcript_text is what's printed on screen — with deliberate substitutions
        "transcript_text": "The Antarctic ice sheet has been gaining mass at an accelerating rate since the early 1980s, with most of the loss concentrated in East Antarctica where cooling ocean currents are eroding the floating ice shelves that buttress coastal glaciers.",
        # word-index errors (0-based, counting whitespace-split tokens of transcript_text)
        "errors": [5, 12, 17, 19, 33],
        "explanation": "Word 5 ('gaining' vs. 'losing'), word 12 ('1980s' vs. '1990s'), word 17 ('East' vs. 'West'), word 19 ('cooling' vs. 'warming'), and word 33 ('coastal' vs. 'inland') all differ between the transcript and the audio.",
        "trap": "Read the transcript ahead and predict likely substitution points (dates, directions, polarity words). Highlight only what differed — over-highlighting incurs negative marking.",
    },
    {
        "id": "l-hiw-002",
        "section": "listening",
        "type": "lst_hiw",
        "topic": "academic lecture",
        "audio_text": "Anthropologists who study small-scale societies have documented a remarkable diversity of marriage and family arrangements, and the pattern that holds is not monogamy but flexibility: different communities adopt different rules in response to ecological pressure, resource scarcity, and historical contact with neighbours.",
        "transcript_text": "Anthropologists who study large-scale societies have documented a remarkable uniformity of marriage and family arrangements, and the pattern that holds is not monogamy but rigidity: different communities adopt similar rules in response to ecological pressure, resource abundance, and historical isolation from neighbours.",
        "errors": [3, 9, 20, 24, 31, 34],
        "explanation": "'large-scale' (vs. small-scale), 'uniformity' (vs. diversity), 'rigidity' (vs. flexibility), 'similar' (vs. different), 'abundance' (vs. scarcity), 'isolation' (vs. contact) all differ. The transcript reverses the polarity of nearly every claim.",
        "trap": "Mass-polarity-reversal questions reward listeners who note the direction of every claim in the audio. Don't get distracted by the unchanged words — about 80% of the transcript matches, and your job is to spot the 20%.",
    },
    {
        "id": "l-hiw-003",
        "section": "listening",
        "type": "lst_hiw",
        "topic": "academic lecture",
        "audio_text": "Renewable hydrogen is produced by passing electricity through water to split it into hydrogen and oxygen, a process called electrolysis. The hydrogen can then be stored, transported, and burned in fuel cells with water as the only emission, which makes it attractive for sectors like steel manufacturing and heavy transport that are difficult to electrify directly.",
        "transcript_text": "Renewable hydrogen is produced by passing electricity through water to split it into hydrogen and nitrogen, a process called electrolysis. The hydrogen can then be stored, transported, and burned in fuel cells with carbon as the only emission, which makes it attractive for sectors like coal manufacturing and light transport that are difficult to electrify directly.",
        "errors": [14, 27, 35, 38],
        "explanation": "'nitrogen' (vs. oxygen), 'carbon' (vs. water), 'coal' (vs. steel), 'light' (vs. heavy) differ between the transcript and the spoken audio.",
        "trap": "Three of the four substitutions are technically nonsensical (electrolysis doesn't produce nitrogen, fuel cells don't emit carbon). Domain knowledge helps you predict where the transcript is likely to be wrong, but always rely on what you actually hear.",
    },
]


# ---------------------------------------------------------------------------
# 3. Tips for the new task types
# ---------------------------------------------------------------------------
NEW_TIPS = {
    "reading_r_fib": [
        {"cat": "Strategy", "tip": "The word bank is shared across all blanks AND has distractors. Don't lock in a word at the first plausible blank — scan all blanks first, then place the highest-confidence picks before the borderline ones."},
        {"cat": "Tricks", "tip": "Two of the distractor words usually share a root with a correct answer (e.g. 'confirmed' vs. 'challenged'). Read the surrounding clause for direction words like 'instead' or 'however' that flip your choice."},
        {"cat": "Time", "tip": "Budget ~90 seconds. If you're stuck on one blank, place your best guess and move on — partial credit is awarded per blank."},
    ],
    "reading_mcq_multi": [
        {"cat": "Strategy", "tip": "Negative marking: you LOSE a point for every wrong tick. If you're unsure between three options for two slots, pick only the two you're certain of — leaving a slot empty beats ticking a wrong option."},
        {"cat": "Tricks", "tip": "Distractors are often phrased as the absolutist version of an actual claim ('all', 'always', 'eliminates' instead of 'reduces'). Treat extremity words as red flags."},
        {"cat": "Tricks", "tip": "Another classic distractor: a true fact from the passage put on the WRONG side of the question. Re-read the question stem — is it asking for benefits, drawbacks, supporting evidence, or counter-arguments?"},
    ],
    "listening_lst_mcq_multi": [
        {"cat": "Strategy", "tip": "Same negative-marking rule as Reading MCQ-Multi. Don't tick options just because the words appeared in the audio — distractors lift vocabulary directly from the lecture but attach it to the wrong claim."},
        {"cat": "Tricks", "tip": "While listening, note 2-3 specific facts. Then on the options, treat any option that doesn't match one of your notes as a likely distractor."},
    ],
    "listening_lst_fib": [
        {"cat": "Strategy", "tip": "Each blank is graded as an exact-match against the audio word. Synonyms do NOT count. Write what you heard, not what feels natural."},
        {"cat": "Tricks", "tip": "Most blanks are content words (nouns, verbs, adjectives) — not 'the', 'and', 'a'. The grammar of the surrounding sentence usually narrows the part of speech you should listen for."},
        {"cat": "Time", "tip": "Audio plays once. Use the first pass to fill what you catch confidently; on the second listen — if there is one — focus only on missing blanks."},
    ],
    "listening_lst_hcs": [
        {"cat": "Strategy", "tip": "The wrong summary options usually mirror the lecture's vocabulary but reverse the conclusion. Anchor on the lecturer's main argument (often the closing sentence), not on which option shares the most words with the audio."},
        {"cat": "Tricks", "tip": "Eliminate before you select: one option will usually overstate ('always', 'never', 'entirely'), one will contradict the lecture's main thrust, one will pick a side detail and inflate it. The remaining option is your answer."},
    ],
    "listening_lst_smw": [
        {"cat": "Strategy", "tip": "The lecture is essentially building toward the missing word — track the argument as it develops, not just the surface vocabulary. The answer is usually 'the natural completion of the lecturer's thought'."},
        {"cat": "Tricks", "tip": "All four options will fit grammatically. The distinction is semantic — only one fits the topic and the lecturer's direction."},
    ],
    "listening_lst_hiw": [
        {"cat": "Strategy", "tip": "Read the transcript on screen FIRST, before audio starts. Predict likely substitution points: numbers, directions, polarity words ('rising/falling', 'East/West'), and named entities."},
        {"cat": "Tricks", "tip": "Negative marking: every wrong word you click subtracts a point. If you're not sure a word differs, do NOT click it."},
        {"cat": "Tricks", "tip": "Audio plays once. Match word-by-word as you listen — when the transcript word doesn't match what you hear, mark it immediately and keep tracking."},
    ],
    # While we're here, give describe_image proper tips now that it has real images.
    "speaking_describe_image": [
        {"cat": "Strategy", "tip": "25-second monologue with a 4-sentence template: (1) what kind of image and what it shows; (2) the most striking feature; (3) one specific data point; (4) overall conclusion or implication."},
        {"cat": "Tricks", "tip": "Always name at least two specific values (percentages, years, places). Vague filler kills the content score even if your fluency is perfect."},
        {"cat": "Tricks", "tip": "For maps, contrast WHAT CHANGED with WHAT'S PRESERVED. For pie charts, name the largest and smallest slices first. For line graphs, identify the leading and trailing line, then describe the gap between them."},
    ],
}


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------

def upsert_questions(bank: dict, test_id: str, new_qs: list[dict]) -> tuple[int, int]:
    """Replace any existing question with the same id, otherwise append."""
    existing = bank["tests"][test_id]["questions"]
    by_id = {q["id"]: i for i, q in enumerate(existing)}
    replaced = 0
    added = 0
    for q in new_qs:
        if q["id"] in by_id:
            existing[by_id[q["id"]]] = q
            replaced += 1
        else:
            existing.append(q)
            added += 1
    return replaced, added


def update_describe_image(bank: dict) -> int:
    """Patch the 6 existing describe_image questions with image_svg + cleaned prompt."""
    by_id = {}
    qs = bank["tests"]["pte"]["questions"]
    for i, q in enumerate(qs):
        if q.get("type") == "describe_image":
            by_id[q["id"]] = i
    n = 0
    for update in DESCRIBE_IMAGE_UPDATES:
        if update["id"] not in by_id:
            print(f"WARN: describe_image {update['id']} not found in bank")
            continue
        q = qs[by_id[update["id"]]]
        q["image_svg"] = update["image_svg"]
        q["prompt"] = update["prompt"]
        q["rubric"] = update["rubric"]
        q["grading_notes"] = update["grading_notes"]
        n += 1
    return n


def main() -> None:
    bank = json.loads(BANK.read_text())

    # 1. Describe Image
    n_di = update_describe_image(bank)

    # 2. New question types — all PTE
    counts = {}
    for label, qs in [
        ("r_fib", R_FIB),
        ("mcq_multi", MCQ_MULTI),
        ("lst_mcq_multi", LST_MCQ_MULTI),
        ("lst_fib", LST_FIB),
        ("lst_hcs", LST_HCS),
        ("lst_smw", LST_SMW),
        ("lst_hiw", LST_HIW),
    ]:
        replaced, added = upsert_questions(bank, "pte", qs)
        counts[label] = (replaced, added)

    # 3. Tips — merge into pte tips dict
    pte_tips = bank["tests"]["pte"].setdefault("tips", {})
    for key, items in NEW_TIPS.items():
        pte_tips[key] = items

    BANK.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n")

    print(f"describe_image: upgraded {n_di} questions with SVG visuals")
    for label, (r, a) in counts.items():
        print(f"  {label:18s} replaced={r} added={a}")


if __name__ == "__main__":
    main()
