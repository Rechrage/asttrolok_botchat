# api/auth.py

import requests
import os

client_id = "9f02dd49-4ab8-4ab3-b88f-fc90e2021265"
client_secret = "r74VQL21dE9YMHsDpKKvf7H3UOMmP6DRtRPWt2gI"

def get_access_token():
    url = "https://api.prokerala.com/token"
    data = {"grant_type": "client_credentials"}
    response = requests.post(url, data=data, auth=(client_id, client_secret))
    if response.status_code == 200:
        return response.json().get("access_token")
    return None
