import requests
import os
import json
from dotenv import load_dotenv

load_dotenv('backend/.env')
token = os.getenv("GITHUB_TOKEN")
headers = {"Authorization": f"token {token}"} if token else {}

user = "CodeWithHarry"
res = requests.get(f"https://api.github.com/users/{user}", headers=headers)
print(json.dumps(res.json(), indent=2))
