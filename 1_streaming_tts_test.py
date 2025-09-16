from dotenv import load_dotenv 
import os

load_dotenv()  # reads .env and sets environment variables 

api_key = os.getenv("OPENAI_API_KEY")

if api_key is None: print("API key not found.")
else: print("API key found:")

print(api_key)