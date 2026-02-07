import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

# Load env vars
load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
model = os.getenv("OPENROUTER_MODEL", "arcee-ai/trinity-large-preview:free")

print(f"Testing connection to OpenRouter...")
print(f"Model: {model}")
print(f"API Key present: {bool(api_key)}")

if not api_key:
    print("ERROR: OPENROUTER_API_KEY is missing in .env")
    sys.exit(1)

try:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        timeout=30.0,
    )

    print("Sending message: 'hi, how are you'")
    
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": "hi, how are you"}
        ],
    )

    response = completion.choices[0].message.content
    print("\n--- RESPONSE FROM LLM ---")
    print(response)
    print("\n-------------------------")
    print("SUCCESS: Connection verified.")

except Exception as e:
    print(f"\nERROR: Connection failed.")
    print(e)
    sys.exit(1)
