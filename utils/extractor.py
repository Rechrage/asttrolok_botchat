# utils/extractor.py
import re
from dateutil import parser

def extract_birth_details(text):
    try:
        dt_obj = parser.parse(text, fuzzy=True)
    except Exception:
        return None

    time_pattern = r'(\d{1,2}:\d{2})'
    if not re.search(time_pattern, text):
        return None

    year, month, day, hour, minute = dt_obj.year, dt_obj.month, dt_obj.day, dt_obj.hour, dt_obj.minute

    location = None
    location_match = re.search(r'(?:in|at)\s+([A-Za-z .,\-]+)', text, re.IGNORECASE)
    if location_match:
        location = location_match.group(1).strip()
    else:
        words = text.strip().split()
        for size in range(3, 0, -1):
            candidate = ' '.join(words[-size:])
            if not re.search(r'\d', candidate):
                location = candidate
                break

    city = district = state = country = None
    if location:
        parts = [p.strip() for p in location.split(',')]
        if len(parts) > 0:
            city = parts[0]
        if len(parts) > 1:
            district = parts[1]
        if len(parts) > 2:
            state = parts[2]
        if len(parts) > 3:
            country = parts[3]

    return {
        "year": year,
        "month": month,
        "day": day,
        "hour": hour,
        "minute": minute,
        "city": city,
        "district": district,
        "state": state,
        "country": country
    }
