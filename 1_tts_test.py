from dotenv import load_dotenv
import os
import json
import requests

# 1) Load OPENAI_API_KEY from .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY not found. Put it in your .env file.")

# 2) Prepare the request
url = "https://api.openai.com/v1/audio/speech"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}
payload = {
    "model": "gpt-4o-mini-tts",
    "voice": "alloy",
    "input": "This class is pretty dang hard",
    "response_format": "mp3",
}

# 3) Send and save as say.mp3
with requests.post(url, headers=headers, data=json.dumps(payload), stream=True) as resp:
    resp.raise_for_status()
    with open("say_python.mp3", "wb") as f:
        for chunk in resp.iter_content(8192):
            if chunk:
                f.write(chunk)

print("Saved to say.mp3")
