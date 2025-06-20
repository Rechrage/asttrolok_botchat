import os
import json
import requests
from datetime import datetime as dt, timezone
import xml.etree.ElementTree as ET
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from utils.cleaner import delete_file_later
from utils.prokerala import get_access_token, get_lagna_chart, get_dasha_periods,get_planet_position


EXPIRE_SECONDS = 620


def safe_geocode(geolocator, location_str, attempts=3):
    for _ in range(attempts):
        try:
            return geolocator.geocode(location_str, timeout=10)
        except (GeocoderTimedOut, GeocoderUnavailable):
            continue
    return None


import xml.etree.ElementTree as ET
from math import hypot

def parse_kundli_svg(svg_content):
    root = ET.fromstring(svg_content)

    rashis = []
    planets = []
    asc_coord = None

    for elem in root.iter():
        if elem.tag.endswith('text') and elem.text:
            text = elem.text.strip()
            x, y = float(elem.attrib['x']), float(elem.attrib['y'])

            if text.isdigit() and 1 <= int(text) <= 12:
                rashis.append({'rashi': text, 'x': x, 'y': y})
            elif text == "Asc":
                asc_coord = (x, y)
                planets.append({'planet': text, 'x': x, 'y': y})
            elif len(text) <= 3 and not text.isdigit():
                planets.append({'planet': text, 'x': x, 'y': y})

    if not asc_coord:
        raise ValueError("Ascendant not found in SVG!")

    # Step 1: Sort rashis clockwise by their appearance
    # We'll find the rashi block closest to Asc — that’s House 1
    rashi_with_distance = []
    for r in rashis:
        dist = hypot(r['x'] - asc_coord[0], r['y'] - asc_coord[1])
        rashi_with_distance.append((dist, r))

    rashi_with_distance.sort(key=lambda x: x[0])  # closest = first house

    # Find index of closest box
    asc_index = rashis.index(rashi_with_distance[0][1])

    # Rotate rashis list so that index = 0 is House 1
    rashis_rotated = rashis[asc_index:] + rashis[:asc_index]

    # Build house map
    house_map = {}
    for i, r in enumerate(rashis_rotated):
        house_no = i + 1
        house_map[house_no] = {
            'house': house_no,
            'rashi_no': r['rashi'],
            'center': (r['x'], r['y']),
            'planets': []
        }

    # Assign each planet to the closest house box
    for p in planets:
        px, py = p['x'], p['y']
        closest_house = min(house_map.values(), key=lambda h: (h['center'][0] - px) ** 2 + (h['center'][1] - py) ** 2)
        closest_house['planets'].append(p['planet'])

    # Remove center data
    for h in house_map.values():
        h.pop('center')

    return house_map


def format_dasha_periods(dasha_data):
    summary = ""
    for maha in dasha_data["data"]["dasha_periods"]:
        summary += f"🔵 Mahadasha: {maha['name']} ({maha['start']} to {maha['end']})\n"
        for antar in maha.get("antardasha", []):
            summary += f"  🔸 Antardasha: {antar['name']} ({antar['start']} to {antar['end']})\n"
            for pratyantar in antar.get("pratyantardasha", []):
                summary += f"    ▫️ Pratyantardasha: {pratyantar['name']} ({pratyantar['start']} to {pratyantar['end']})\n"
    return summary


def get_planet_positions_from_data_ws(year, month, day, hour, minute, city, district=None, state=None, country=None, output_file=None):
    # print('get_planet_positions_from_data_ws')
    location_str = ', '.join(filter(None, [city, district, state, country]))
    geolocator = Nominatim(user_agent="astro_app")
    location = safe_geocode(geolocator, location_str)
    if not location:
        return {"error": f"Location not found: {location_str}"}

    latitude = float(location.latitude)
    longitude = float(location.longitude)
    dt_obj = dt(year, month, day, hour, minute)
    iso_datetime = dt_obj.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    token = get_access_token()
    # print(token)
    if not token:
        return {"error": "Failed to fetch Prokerala token"}
    headers = {"Authorization": f"Bearer {token}"}
    try:
        chart_res = get_lagna_chart(token, latitude, longitude, dt_obj)
        planet_position = get_planet_position(token, latitude, longitude, dt_obj)
        # print(planet_position["data"]["planet_position"])
    except Exception as e:
        return {"error": "Failed to fetch chart", "details": str(e)}

    # breakpoint()
    parse_kundli_svg1 = parse_kundli_svg(chart_res)
    # print("Lagna chart :",  parse_kundli_svg1)
  
    # 🟢 Kundli data paste here (chart_svg from Prokerala)
    kundli = parse_kundli_svg1

    # 🧠 Rashi Number to Name Mapping
    rashi_names = {
        "1": "Mesh (Aries)", "2": "Vrishabh (Taurus)", "3": "Mithun (Gemini)",
        "4": "Kark (Cancer)", "5": "Singh (Leo)", "6": "Kanya (Virgo)",
        "7": "Tula (Libra)", "8": "Vrishchik (Scorpio)", "9": "Dhanu (Sagittarius)",
        "10": "Makar (Capricorn)", "11": "Kumbh (Aquarius)", "12": "Meen (Pisces)"
    }

    # 📜 Planet full forms
    planet_names = {
        "Su": "Surya", "Mo": "Chandra", "Ma": "Mangal", "Me": "Budh", "Ve": "Shukra",
        "Sa": "Shani", "Ju": "Guru", "Ra": "Rahu", "Ke": "Ketu", "Asc": "Lagna"
    }

    # 📤 Output list
    output_data = []

    # 🔁 Loop through chart and generate Q&A
    for house_no, details in kundli.items():
        house = details["house"]
        rashi_no = details["rashi_no"]
        rashi_name = rashi_names.get(rashi_no, f"Rashi {rashi_no}")
        planets = details["planets"]

        for planet in planets:
            planet_name = planet_names.get(planet, planet)

            # Prompt and Completion
            prompt = f"User: {planet_name} kaha hai?\nBot:"
            completion = f" {planet_name} aapke {house}th house me hai jo ki {rashi_name} rashi me sthit hai."

            output_data.append({
                "prompt": prompt,
                "completion": completion
            })

    # 💾 Save to file
    with open("kundli_prompts.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    planet_position = json.loads(planet_position)
    plant_new = planet_position["data"]["planet_position"]
    # print(plant_new)

    if output_file:
        with open(output_file, "w") as f:
            json.dump({
                "chart_svg": parse_kundli_svg1,
                "planet_position": plant_new
            }, f, indent=2)
        # delete_file_later(output_file, EXPIRE_SECONDS)

    # plant_new = planet_position["data"]["planet_position"]

    return {"svg": chart_res,"planet_position": plant_new}


def kundali_svg_to_text(svg_text):
    return "Lagna in Virgo, Venus in 7th house, Jupiter in 5th house, Mahadasha Venus, Antar Dasha Mars"
