import json
import time
import traceback

from google import genai
from google.genai import types

from app.core.config import settings


class CodePlannerService:

    MODEL = "gemini-3.5-flash"
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
        repository_files: list[str],
    ) -> dict:

        if not user_request.strip():
            raise ValueError(
                "User request cannot be empty"
            )

        if not isinstance(repository_files, list):
            raise ValueError(
                "repository_files must be a list"
            )

        context = cls._build_context(
            retrieved_chunks
        )

        repository_inventory = cls._build_repository_inventory(
            repository_files
        )

        prompt = f"""
You are Syntra, an autonomous software engineering agent.

Analyze the user's requested change using the provided repository
inventory and relevant repository context.

USER REQUEST:
{user_request}

REPOSITORY FILE INVENTORY:
{repository_inventory}

RELEVANT REPOSITORY CONTEXT:
{context}

Create a precise implementation plan.

IMPORTANT FILE EXISTENCE RULES:

1. The REPOSITORY FILE INVENTORY is the authoritative source for
   determining whether a file exists.

2. If a requested file exists in the repository inventory:
   - Put it in "files_to_modify".
   - Do not put it in "files_to_create".

3. If a requested file does NOT exist in the repository inventory:
   - You MAY put it in "files_to_create" if creating that file is
     directly required by the user's request.
   - Do not claim that an existing file should be modified if it does
     not exist.

4. For documentation requests:
   - If README.md exists, modify README.md.
   - If README.md does not exist and the user requests a README or
     documentation that requires one, create README.md.
   - A README.md may be created using information available from the
     repository inventory and relevant repository context.
   - Do not invent project features that are unsupported by the
     repository context.
   - If important information is unavailable, explicitly mention it
     in assumptions.

5. File creation is allowed when it is directly required by the
   user's request.

6. Do not invent unrelated files or project structure.

7. Only propose changes that are supported by the repository
   inventory and repository context.

8. Do not write the final code.

9. Identify the exact files that should be modified or created.

10. Include validation steps.

11. Identify potential risks.

12. Do not invent business requirements.

13. If the request cannot be safely supported by the available
    repository information, do not invent a solution. Explain the
    limitation in assumptions.

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
                print("\n" + "=" * 80)
                print("SYNTRA PLANNER: CALLING GEMINI")
                print("=" * 80)

                result = cls.client.models.generate_content(
                    model=cls.MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        max_output_tokens=4096,
                    ),
                )

                print("SYNTRA PLANNER: GEMINI RETURNED")
                print(f"RESULT TYPE: {type(result)}")
                print(f"RESULT: {result}")

                if result is None:
                    raise RuntimeError(
                        "Gemini returned None instead of a response"
                    )

                if not result.text:
                    raise RuntimeError(
                        "Gemini returned an empty planning response"
                    )

                print("SYNTRA PLANNER: RESPONSE TEXT RECEIVED")
                print(result.text)

                try:
                    plan = json.loads(result.text)
                except json.JSONDecodeError as exc:
                    raise RuntimeError(
                        "Gemini returned invalid JSON"
                    ) from exc

                print("SYNTRA PLANNER: JSON PARSED")
                print(f"PLAN TYPE: {type(plan)}")
                print(f"PLAN: {plan}")

                cls._validate_plan(plan)

                print("SYNTRA PLANNER: VALIDATION PASSED")
                print("=" * 80)

                return plan

            except Exception as exc:
                print("\n" + "=" * 80)
                print("SYNTRA PLANNER INTERNAL ERROR")
                print("=" * 80)
                print(f"ERROR TYPE: {type(exc).__name__}")
                print(f"ERROR: {repr(exc)}")
                print("\nTRACEBACK:")
                traceback.print_exc()
                print("=" * 80)

                last_error = exc

                if "503" not in str(exc):
                    raise

                if attempt >= cls.MAX_RETRIES:
                    break

                delay = cls.RETRY_DELAYS[attempt]

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
                "No relevant repository context was retrieved."
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

        return "\n".join(sections)

    @staticmethod
    def _build_repository_inventory(
        repository_files: list[str],
    ) -> str:

        if not repository_files:
            return (
                "No repository files were discovered."
            )

        normalized_files = sorted(
            {
                file_path.strip()
                for file_path in repository_files
                if isinstance(file_path, str)
                and file_path.strip()
            }
        )

        if not normalized_files:
            return (
                "No repository files were discovered."
            )

        return "\n".join(
            f"- {file_path}"
            for file_path in normalized_files
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

        for item in plan["files_to_modify"]:
            if not isinstance(item, dict):
                raise RuntimeError(
                    "Each files_to_modify item must be an object"
                )

            if not isinstance(
                item.get("file_path"),
                str,
            ):
                raise RuntimeError(
                    "Each files_to_modify item requires a string file_path"
                )

            if not isinstance(
                item.get("reason"),
                str,
            ):
                raise RuntimeError(
                    "Each files_to_modify item requires a string reason"
                )

            if not isinstance(
                item.get("changes"),
                list,
            ):
                raise RuntimeError(
                    "Each files_to_modify item requires a changes list"
                )

        for item in plan["files_to_create"]:
            if not isinstance(item, dict):
                raise RuntimeError(
                    "Each files_to_create item must be an object"
                )

            if not isinstance(
                item.get("file_path"),
                str,
            ):
                raise RuntimeError(
                    "Each files_to_create item requires a string file_path"
                )

            if not isinstance(
                item.get("reason"),
                str,
            ):
                raise RuntimeError(
                    "Each files_to_create item requires a string reason"
                )