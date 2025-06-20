# utils/prompts.py

def build_svg_prompt(svg, dasha, question):
    return f"""
User's Vedic birth chart data is:
{svg}
Dasha Periods:
{dasha}
User's question: {question}

Please answer the question based only on this chart data and Dasha periods. Keep the tone clear and friendly. Include Vedic astrology concepts where relevant.
"""

def build_marriage_prompt(kundali_text, question):
    return f"""
You are a Jyotish astrologer. Analyze the following kundali:
{kundali_text}
User question: {question}

Focus on:
- 7th house (marriage)
- Venus (Shukra)
- Jupiter (Guru)
- Mahadasha/Antardasha
Give marriage prediction with classical logic.
"""

def build_default_prompt(question):
    return f"""
You are AlokGPT — a Jyotish assistant trained using Asttrolok's modules only...
User question: {question}
"""
