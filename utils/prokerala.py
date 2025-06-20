import os
import requests
import json
from datetime import datetime, timezone

# You may want to store this securely instead of hardcoding
PROKERALA_CLIENT_ID = os.getenv("PROKERALA_CLIENT_ID")
PROKERALA_CLIENT_SECRET = os.getenv("PROKERALA_CLIENT_SECRET")
TOKEN_URL = "https://api.prokerala.com/token"
url = "https://api.prokerala.com/token"
data = {"grant_type": "client_credentials"}
auth = (os.getenv("PROKERALA_CLIENT_ID"), os.getenv("PROKERALA_CLIENT_SECRET"))
res = requests.post(url, data=data, auth=auth)
# return res.json().get("access_token") if res.status_code == 200 else None

def get_access_token():
    try:
        response = requests.post(
            TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(PROKERALA_CLIENT_ID, PROKERALA_CLIENT_SECRET)
        )
        return response.json().get("access_token") if response.status_code == 200 else None
    except Exception:
        return None


def get_lagna_chart(token, latitude, longitude, dt_obj, ayanamsa=1):
    iso_datetime = dt_obj.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get("https://api.prokerala.com/v2/astrology/chart", headers=headers, params={
        "ayanamsa": ayanamsa,
        "coordinates": f"{latitude},{longitude}",
        "datetime": iso_datetime,
        "chart_type": "lagna",
        "chart_style": "north-indian",
        "format": "svg"
    })
   
    if response.status_code == 200:
        # print("Lagna chart :",  response1.text)
        return response.text
    else:
        print("Lagna chart error:", response.status_code, response.text)
        raise Exception(f"Lagna chart fetch failed: {response.text}")
        
def get_planet_position(token, latitude, longitude, dt_obj, ayanamsa=1):
    iso_datetime = dt_obj.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get("https://api.prokerala.com/v2/astrology/planet-position", headers=headers, params={
        "ayanamsa": ayanamsa,
        "coordinates": f"{latitude},{longitude}",
        "datetime": iso_datetime
    })
   
    if response.status_code == 200:
        # print("Lagna chart :",  response1.text)
        return response.text
    else:
        print("Lagna chart error:", response.status_code, response.text)
        raise Exception(f"Lagna chart fetch failed: {response.text}")


    # return call_prokerala_api(token, "/v2/astrology/planet-position", {
    #     "coordinates": f"{latitude},{longitude}",
    #     "datetime": get_iso_datetime(dt_obj)
    # })

def get_dasha_periods(token, latitude, longitude, dt_obj, ayanamsa=1):
    iso_datetime = dt_obj.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get("https://api.prokerala.com/v2/astrology/dasha-periods", headers=headers, params={
        "ayanamsa": ayanamsa,
        "coordinates": f"{latitude},{longitude}",
        "datetime": iso_datetime
    })
    if response.status_code == 200:
        print("Lagna dasa :",  response.text)
        return response.json()
    else:
        raise Exception(f"Dasha periods fetch failed: {response.text}")
