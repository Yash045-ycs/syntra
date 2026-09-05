from google import genai
from app.core.config import settings

client = genai.Client(
    api_key=settings.GEMINI_API_KEY,
    http_options={"timeout": 30000}
)

models = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
]

for model in models:
    print(f"\nTesting: {model}")

    try:
        response = client.models.generate_content(
            model=model,
            contents="Reply with exactly: SYNTRA_OK",
        )

        print("SUCCESS")
        print(response.text)

    except Exception as exc:
        print("FAILED")
        print(type(exc).__name__)
        print(exc)