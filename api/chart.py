# api/chart.py

import requests
from .auth import get_access_token

API_URL = "https://api.prokerala.com/v2/astrology/chart"
token = get_access_token()

def get_chart_svg(
    ayanamsa: int,
    latitude: float,
    longitude: float,
    datetime_str: str,
    chart_type: str = "lagna",
    chart_style: str = "north-indian",
    language: str = "en"
):
    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {
        "ayanamsa": ayanamsa,
        "coordinates": f"{latitude},{longitude}",
        "datetime": datetime_str,
        "chart_type": chart_type,
        "chart_style": chart_style,
        "format": "svg",
        "la": language
    }

    response = requests.get(API_URL, headers=headers, params=params)
    try:
        response.raise_for_status()
    except requests.HTTPError as http_err:
        if "application/json" in response.headers.get("Content-Type", ""):
            return {"errors": response.json().get("errors", [{"title": "Unknown error"}])}
        else:
            return {"errors": [{"title": "HTTP Error", "detail": str(http_err)}]}

    return {"svg": response.text}
