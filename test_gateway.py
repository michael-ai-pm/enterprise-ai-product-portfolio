import os
from dotenv import load_dotenv
import litellm

load_dotenv()

response = litellm.completion(
    model="openrouter/openrouter/free",
    messages=[{"role": "user", "content": "Reply with exactly: gateway works"}],
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

print(response.choices[0].message.content)