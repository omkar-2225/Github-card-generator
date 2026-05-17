import httpx
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="backend/.env")
api_key = os.getenv("GOOGLE_API_KEY")

def list_models():
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    response = httpx.get(url)
    print(response.text)

if __name__ == "__main__":
    list_models()
