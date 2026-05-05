import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

print("Checking available models...")
for model in client.models.list():
    if "3" in model.name:
        print(model.name)
