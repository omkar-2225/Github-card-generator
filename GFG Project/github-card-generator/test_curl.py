import requests
import json

url = "http://localhost:8080/generate"
data = {"username": "defunkt"}

try:
    response = requests.post(url, json=data)
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
