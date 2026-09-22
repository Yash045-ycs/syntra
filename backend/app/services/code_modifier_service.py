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
- Follow the implementation plan exactly.
- Modify only files listed in files_to_modify.
- Create only files listed in files_to_create.
- If the implementation plan explicitly requests a file to be created,
  you may create that file even when it does not exist in the provided
  source files.
- Preserve existing functionality unless the request requires changing it.
- Do not invent unavailable project structure.
- Do not modify dependencies unless explicitly required.
- Return complete replacement content for every modified file.
- Return complete content for every newly created file.
- For README.md creation, generate a concise and accurate README based
  only on the repository context, implementation plan, and user request.
- Do not claim features, technologies, commands, APIs, or architecture
  that are not supported by the provided context.
- Do not include markdown code fences around file content.
- Do not explain the changes outside the JSON response.
- Never include secrets, credentials, API keys, or tokens.
- If a requested modification cannot be safely implemented from the
  provided context, do not invent code.
- If a requested new file cannot be safely created from the available
  context, do not create it and explain why in files_not_modified or
  warnings.

Return ONLY valid JSON:

{{
  "changes": [
    {{
      "file_path": "string",
      "action": "modify",
      "reason": "string",
      "content": "complete file content"
    }},
    {{
      "file_path": "string",
      "action": "create",
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

                if result is None:
                    raise RuntimeError(
                        "Gemini returned None instead of a response"
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
                    plan,
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
        plan: dict,
        source_files: dict[str, str],
    ) -> None:

        required_fields = {
            "changes",
            "files_not_modified",
            "warnings",
        }

        if not isinstance(changes, dict):
            raise RuntimeError(
                "Modification response must be an object"
            )

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

        files_to_modify = {
            item.get("file_path")
            for item in plan.get("files_to_modify", [])
            if isinstance(item, dict)
        }

        files_to_create = {
            item.get("file_path")
            for item in plan.get("files_to_create", [])
            if isinstance(item, dict)
        }

        files_to_modify.discard(None)
        files_to_create.discard(None)

        if files_to_modify & files_to_create:
            raise RuntimeError(
                "A file cannot appear in both files_to_modify and files_to_create"
            )

        existing_files = set(source_files.keys())

        for change in changes["changes"]:

            if not isinstance(change, dict):
                raise RuntimeError(
                    "Each change must be an object"
                )

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

            file_path = change["file_path"]
            action = change["action"]

            if not isinstance(file_path, str) or not file_path.strip():
                raise RuntimeError(
                    "file_path must be a non-empty string"
                )

            if not isinstance(change["reason"], str):
                raise RuntimeError(
                    f"Reason must be a string for {file_path}"
                )

            if not isinstance(change["content"], str):
                raise RuntimeError(
                    f"Content must be a string for {file_path}"
                )

            if action == "modify":

                if file_path not in existing_files:
                    raise RuntimeError(
                        f"Cannot modify unavailable file: {file_path}"
                    )

                if file_path not in files_to_modify:
                    raise RuntimeError(
                        f"Modification attempted on unauthorized file: {file_path}"
                    )

            elif action == "create":

                if file_path in existing_files:
                    raise RuntimeError(
                        f"Cannot create file that already exists: {file_path}"
                    )

                if file_path not in files_to_create:
                    raise RuntimeError(
                        f"Creation attempted on unauthorized file: {file_path}"
                    )

            else:
                raise RuntimeError(
                    f"Unsupported action: {action}"
                )
