import json
import time

from google import genai
from google.genai import types
from google.genai.errors import ServerError, ClientError

from app.core.config import settings


class AIService:
    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options={
            "timeout": 30000
        }
    )

    MODELS = [
        "gemini-3.5-flash",
        "gemini-3.1-flash-lite",
    ]

    @classmethod
    def ask(cls, prompt: str) -> str:
        for model in cls.MODELS:
            print(f"[AI] Trying model: {model}")

            for attempt in range(2):
                try:
                    print(
                        f"[AI] Sending request "
                        f"(attempt {attempt + 1}/2)"
                    )

                    response = cls.client.models.generate_content(
                        model=model,
                        contents=prompt,
                    )

                    if not response.text:
                        raise RuntimeError(
                            "Gemini returned an empty response"
                        )

                    print(
                        f"[AI] Response received from {model}"
                    )

                    return response.text

                except ClientError as exc:
                    print(
                        f"[AI] {model} client error: {exc}"
                    )

                    if "429" in str(exc):
                        print(
                            f"[AI] Quota exceeded for {model}"
                        )
                        break

                    if attempt == 0:
                        time.sleep(2)

                except ServerError as exc:
                    print(
                        f"[AI] {model} unavailable: {exc}"
                    )

                    if attempt == 0:
                        time.sleep(2)

            print(
                "[AI] Moving to fallback model"
            )

        raise RuntimeError(
            "All configured Gemini models are currently unavailable "
            "or their free-tier quotas have been exhausted"
        )

    @classmethod
    def analyze_codebase(cls, context: dict) -> str:
        prompt = f"""
You are Syntra, an autonomous AI software engineering agent.

Analyze the following software repository.

Determine:

1. Overall purpose
2. Technology stack
3. Architecture
4. Important files
5. Entry points
6. Database or storage
7. Authentication and authorization
8. API structure
9. Testing structure
10. Important dependencies
11. Areas likely to require changes for future feature requests

Do not modify any code.

Provide a concise technical analysis that another AI agent can use when planning code changes.

Repository information:

{json.dumps(context, indent=2)}
"""
        return cls.ask(prompt)