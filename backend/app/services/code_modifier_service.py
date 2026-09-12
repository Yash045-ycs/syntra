import json
import time

from google import genai
from google.genai import types

from app.core.config import settings


class CodeModifierService:

    MODEL = "gemini-3.6-flash"
    MAX_RETRIES = 4
    RETRY_DELAYS = [5, 10, 20, 40]

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
    )

    @classmethod
    def generate_changes(
        cls,
        user_request: str,
        plan: dict,
        source_files: dict[str, str],
    ) -> dict:

        if not user_request.strip():
            raise ValueError("User request cannot be empty")

        if not isinstance(plan, dict):
            raise ValueError("Plan must be a dictionary")

        context = cls._build_source_context(source_files)

        prompt = f"""
You are Syntra, an autonomous software engineering agent.

Generate precise code modifications based on the user's request,
implementation plan, and provided source files.

USER REQUEST:
{user_request}

IMPLEMENTATION PLAN:
{json.dumps(plan, indent=2)}

SOURCE FILES:
{context}

Rules:
- Modify only files supported by the implementation plan.
- Preserve existing functionality unless the request requires changing it.
- Do not invent unavailable project structure.
- Do not modify dependencies unless explicitly required.
- Return complete replacement content for every modified file.
- Do not include markdown code fences.
- Do not explain the changes outside the JSON response.
- Never include secrets, credentials, API keys, or tokens.
- If the requested change cannot be safely implemented from the provided
  context, return an empty changes list and explain why.

Return ONLY valid JSON:

{{
  "changes": [
    {{
      "file_path": "string",
      "action": "modify",
      "reason": "string",
      "content": "complete file content"
    }}
  ],
  "files_not_modified": [
    {{
      "file_path": "string",
      "reason": "string"
    }}
  ],
  "warnings": [
    "string"
  ]
}}
"""

        last_error = None

        for attempt in range(cls.MAX_RETRIES + 1):
            try:
                result = cls.client.models.generate_content(
                    model=cls.MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                    ),
                )

                if not result.text:
                    raise RuntimeError(
                        "Gemini returned an empty modification response"
                    )

                try:
                    changes = json.loads(result.text)
                except json.JSONDecodeError as exc:
                    raise RuntimeError(
                        "Gemini returned invalid JSON"
                    ) from exc

                cls._validate_changes(
                    changes,
                    source_files,
                )

                return changes

            except Exception as exc:
                last_error = exc

                if "503" not in str(exc):
                    raise

                if attempt >= cls.MAX_RETRIES:
                    break

                time.sleep(cls.RETRY_DELAYS[attempt])

        raise RuntimeError(
            "Gemini remained unavailable after retries"
        ) from last_error

    @staticmethod
    def _build_source_context(
        source_files: dict[str, str],
    ) -> str:

        if not source_files:
            return "No source files were provided."

        sections = []

        for file_path, content in source_files.items():
            sections.append(
                f"""
--- FILE: {file_path} ---
{content}
"""
            )

        return "\n".join(sections)

    @staticmethod
    def _validate_changes(
        changes: dict,
        source_files: dict[str, str],
    ) -> None:

        required_fields = {
            "changes",
            "files_not_modified",
            "warnings",
        }

        missing = required_fields - changes.keys()

        if missing:
            raise RuntimeError(
                f"Modification response missing fields: {sorted(missing)}"
            )

        if not isinstance(changes["changes"], list):
            raise RuntimeError("changes must be a list")

        if not isinstance(changes["files_not_modified"], list):
            raise RuntimeError("files_not_modified must be a list")

        if not isinstance(changes["warnings"], list):
            raise RuntimeError("warnings must be a list")

        allowed_paths = set(source_files.keys())

        for change in changes["changes"]:

            if not isinstance(change, dict):
                raise RuntimeError("Each change must be an object")

            required_change_fields = {
                "file_path",
                "action",
                "reason",
                "content",
            }

            missing_change_fields = (
                required_change_fields - change.keys()
            )

            if missing_change_fields:
                raise RuntimeError(
                    f"Change missing fields: {sorted(missing_change_fields)}"
                )

            if change["action"] != "modify":
                raise RuntimeError(
                    f"Unsupported action: {change['action']}"
                )

            file_path = change["file_path"]

            if file_path not in allowed_paths:
                raise RuntimeError(
                    f"Modification attempted on unauthorized file: {file_path}"
                )

            if not isinstance(change["content"], str):
                raise RuntimeError(
                    f"Content must be a string for {file_path}"
                )