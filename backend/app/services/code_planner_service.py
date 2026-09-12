import json
import time

from google import genai
from google.genai import types

from app.core.config import settings


class CodePlannerService:

    MODEL = "gemini-3.6-flash"
    MAX_RETRIES = 4
    RETRY_DELAYS = [5, 10, 20, 40]

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(
            timeout=120000,
        ),
    )

    @classmethod
    def create_plan(
        cls,
        user_request: str,
        retrieved_chunks: list[dict],
    ) -> dict:

        if not user_request.strip():
            raise ValueError(
                "User request cannot be empty"
            )

        context = cls._build_context(
            retrieved_chunks
        )

        prompt = f"""
You are Syntra, an autonomous software engineering agent.

Analyze the user's requested change using the provided repository context.

USER REQUEST:
{user_request}

REPOSITORY CONTEXT:
{context}

Create a precise implementation plan.

Rules:
- Only propose changes supported by the provided context.
- Identify the exact files that should be modified whenever possible.
- Do not write the final code.
- Do not invent files or project structure.
- Mention assumptions when information is missing.
- Include validation steps.
- Identify potential risks.
- Do not invent business requirements.
- If the request cannot be safely supported by the provided repository
  context, do not invent a solution. State the limitation in assumptions
  and return no file modifications.

Return ONLY valid JSON with this structure:

{{
  "goal": "string",
  "files_to_modify": [
    {{
      "file_path": "string",
      "reason": "string",
      "changes": [
        "string"
      ]
    }}
  ],
  "files_to_create": [
    {{
      "file_path": "string",
      "reason": "string"
    }}
  ],
  "risks": [
    "string"
  ],
  "validation": [
    "string"
  ],
  "assumptions": [
    "string"
  ]
}}
"""

        last_error = None

        for attempt in range(
            cls.MAX_RETRIES + 1
        ):
            try:

                result = (
                    cls.client.models.generate_content(
                        model=cls.MODEL,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            max_output_tokens=4096,
                        ),
                    )
                )

                if not result.text:
                    raise RuntimeError(
                        "Gemini returned an empty planning response"
                    )

                try:
                    plan = json.loads(
                        result.text
                    )
                except json.JSONDecodeError as exc:
                    raise RuntimeError(
                        "Gemini returned invalid JSON"
                    ) from exc

                cls._validate_plan(
                    plan
                )

                return plan

            except Exception as exc:

                last_error = exc

                if "503" not in str(exc):
                    raise

                if attempt >= cls.MAX_RETRIES:
                    break

                delay = cls.RETRY_DELAYS[
                    attempt
                ]

                print(
                    f"[Planner] Gemini unavailable. "
                    f"Retrying in {delay} seconds "
                    f"({attempt + 1}/{cls.MAX_RETRIES})"
                )

                time.sleep(delay)

        raise RuntimeError(
            "Gemini remained unavailable after "
            "planner retries"
        ) from last_error

    @staticmethod
    def _build_context(
        retrieved_chunks,
    ):

        if not retrieved_chunks:
            return (
                "No repository context was retrieved."
            )

        sections = []

        for index, chunk in enumerate(
            retrieved_chunks,
            start=1,
        ):

            sections.append(
                f"""
--- CONTEXT {index} ---
File: {chunk.get("file_path", "unknown")}
Language: {chunk.get("language", "unknown")}
Chunk: {chunk.get("chunk_index", 0)}
Similarity: {chunk.get("similarity", 0)}

{chunk.get("content", "")}
"""
            )

        return "\n".join(
            sections
        )

    @staticmethod
    def _validate_plan(
        plan,
    ):

        required_fields = {
            "goal",
            "files_to_modify",
            "files_to_create",
            "risks",
            "validation",
            "assumptions",
        }

        if not isinstance(
            plan,
            dict,
        ):
            raise RuntimeError(
                "Planning response must be an object"
            )

        missing = (
            required_fields
            - plan.keys()
        )

        if missing:
            raise RuntimeError(
                f"Planning response missing fields: "
                f"{sorted(missing)}"
            )

        if not isinstance(
            plan["goal"],
            str,
        ):
            raise RuntimeError(
                "goal must be a string"
            )

        if not isinstance(
            plan["files_to_modify"],
            list,
        ):
            raise RuntimeError(
                "files_to_modify must be a list"
            )

        if not isinstance(
            plan["files_to_create"],
            list,
        ):
            raise RuntimeError(
                "files_to_create must be a list"
            )

        if not isinstance(
            plan["risks"],
            list,
        ):
            raise RuntimeError(
                "risks must be a list"
            )

        if not isinstance(
            plan["validation"],
            list,
        ):
            raise RuntimeError(
                "validation must be a list"
            )

        if not isinstance(
            plan["assumptions"],
            list,
        ):
            raise RuntimeError(
                "assumptions must be a list"
            )