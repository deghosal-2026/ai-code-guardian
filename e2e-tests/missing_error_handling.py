import json

def parse_config(filepath):
    try:
        with open(filepath) as f:
            return json.load(f)
    except:
        return {}

def fetch_data(url):
    try:
        response = http_client.get(url)
        return response.json()
    except:
        return None
