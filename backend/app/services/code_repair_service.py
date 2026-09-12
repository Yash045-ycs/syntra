import json
import time

from google import genai
from google.genai import types

from app.core.config import settings


class CodeRepairService:

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
    def generate_repair(
        cls,
        user_request: str,
        plan: dict,
        failure_output: str,
        source_files: dict[str, str],
    ) -> dict:

        if not user_request.strip():
            raise ValueError("User request cannot be empty")

        if not isinstance(plan, dict):
            raise ValueError("Plan must be a dictionary")

        if not failure_output.strip():
            raise ValueError("Failure output cannot be empty")

        context = cls._build_source_context(source_files)

        prompt = f"""
You are Syntra, an autonomous software engineering agent.

A code change was already generated and applied to a repository.
The validation tests have failed.

Analyze the failure and generate the smallest safe code correction
required to satisfy the original user request.

ORIGINAL USER REQUEST:
{user_request}

IMPLEMENTATION PLAN:
{json.dumps(plan, indent=2)}

TEST FAILURE:
{failure_output}

CURRENT SOURCE FILES:
{context}

Rules:
- Diagnose the actual failure before proposing a fix.
- Modify only files provided in CURRENT SOURCE FILES.
- Preserve existing functionality.
- Make the smallest reasonable correction.
- Do not modify dependencies unless absolutely required.
- Do not invent unavailable project structure.
- Return complete replacement content for every modified file.
- Do not include markdown code fences.
- Do not include secrets, credentials, API keys, or tokens.
- If the failure cannot be safely fixed from the provided context,
  return an empty changes list and explain why.
- Do not modify files unrelated to the failure.
- Do not infer new business rules, fees, defaults, or behavior that are not supported by the user request, implementation plan, source code, or test failure.
- If the test expectation conflicts with the available requirements, report the conflict instead of inventing a rule.

Return ONLY valid JSON:

{{
  "diagnosis": "string",
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
    max_output_tokens=4096,
),
                )

                if not result.text:
                    raise RuntimeError(
                        "Gemini returned an empty repair response"
                    )

                try:
                    repair = json.loads(result.text)
                except json.JSONDecodeError as exc:
                    raise RuntimeError(
                        "Gemini returned invalid JSON"
                    ) from exc

                cls._validate_repair(
                    repair,
                    source_files,
                    plan,
                )

                return repair

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
    @staticmethod
    def _validate_repair(
        repair: dict,
        source_files: dict[str, str],
        plan: dict,
    ) -> None:

        required_fields = {
            "diagnosis",
            "changes",
            "files_not_modified",
            "warnings",
        }

        missing = required_fields - repair.keys()

        if missing:
            raise RuntimeError(
                f"Repair response missing fields: {sorted(missing)}"
            )

        if not isinstance(repair["diagnosis"], str):
            raise RuntimeError(
                "diagnosis must be a string"
            )

        if not isinstance(repair["changes"], list):
            raise RuntimeError(
                "changes must be a list"
            )

        if not isinstance(repair["files_not_modified"], list):
            raise RuntimeError(
                "files_not_modified must be a list"
            )

        if not isinstance(repair["warnings"], list):
            raise RuntimeError(
                "warnings must be a list"
            )

        allowed_paths = set(source_files.keys())

        planned_paths = {
            item["file_path"]
            for item in plan.get("files_to_modify", [])
            if isinstance(item, dict)
            and isinstance(item.get("file_path"), str)
        }

        planned_paths.update(
            item["file_path"]
            for item in plan.get("files_to_create", [])
            if isinstance(item, dict)
            and isinstance(item.get("file_path"), str)
        )

        for change in repair["changes"]:

            if not isinstance(change, dict):
                raise RuntimeError(
                    "Each repair change must be an object"
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
                    f"Repair change missing fields: {sorted(missing_change_fields)}"
                )

            if change["action"] != "modify":
                raise RuntimeError(
                    f"Unsupported repair action: {change['action']}"
                )

            file_path = change["file_path"]

            if file_path not in allowed_paths:
                raise RuntimeError(
                    f"Repair attempted on unauthorized file: {file_path}"
                )

            if file_path not in planned_paths:
                raise RuntimeError(
                    f"Repair attempted on unplanned file: {file_path}"
                )

            if not isinstance(change["content"], str):
                raise RuntimeError(
                    f"Content must be a string for {file_path}"
                )