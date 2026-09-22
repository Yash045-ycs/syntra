import json
import os

from app.services.ai_service import AIService


class CodeEditorService:

    @classmethod
    def generate_changes(
        cls,
        change_request: str,
        plan: dict,
        context: dict,
    ) -> dict:

        relevant_files = {
            item["file_path"]
            for item in plan.get("files_to_modify", [])
            if "file_path" in item
        }

        relevant_files.update(
            item["file_path"]
            for item in plan.get("tests_to_modify", [])
            if "file_path" in item
        )

        files = [
            file
            for file in context.get("files", [])
            if file.get("path") in relevant_files
        ]

        prompt = f"""
You are Syntra, an autonomous AI software engineering agent.

Modify the existing repository and create any required new files
according to the user's request and implementation plan.

USER REQUEST:
{change_request}

IMPLEMENTATION PLAN:
{json.dumps(plan, indent=2)}

RELEVANT EXISTING FILES:
{json.dumps(files, indent=2)}

FILES TO CREATE:
{json.dumps(plan.get("files_to_create", []), indent=2)}

Rules:

1. Existing files must use action "modify".
2. New files listed in FILES TO CREATE must use action "create".
3. Never create a file unless it is explicitly listed in FILES TO CREATE.
4. Every modified file must exactly match a path from RELEVANT EXISTING FILES.
5. Every created file must exactly match a path from FILES TO CREATE.
6. Preserve existing functionality unless the request requires changing it.
7. Do not remove unrelated code.
8. Preserve the project's existing coding style.
9. Update tests when required by the implementation plan.
10. Return complete file contents for every change.
11. Do not return markdown.
12. Do not use code fences.
13. Never include secrets, credentials, API keys, or tokens.
14. Use relative repository paths only.
15. Return ONLY valid JSON.
16. If no safe change can be generated, return an empty changes list.

For every change, use this exact structure:

{{
  "file_path": "relative/file/path",
  "action": "modify",
  "content": "complete file content"
}}

For newly created files:

{{
  "file_path": "relative/new/file/path",
  "action": "create",
  "content": "complete new file content"
}}

Return exactly:

{{
  "changes": [
    {{
      "file_path": "relative/file/path",
      "action": "modify",
      "content": "complete updated file content"
    }}
  ]
}}
"""

        response = AIService.ask(prompt)

        try:
            result = json.loads(response)

        except json.JSONDecodeError:

            cleaned = response.strip()

            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]

            if cleaned.startswith("```"):
                cleaned = cleaned[3:]

            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            try:
                result = json.loads(cleaned.strip())

            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    "AI returned an invalid code modification response"
                ) from exc

        cls._validate_changes(
            result,
            plan,
            context,
        )

        return result

    @classmethod
    def _validate_changes(
        cls,
        result: dict,
        plan: dict,
        context: dict,
    ) -> None:

        if not isinstance(result, dict):
            raise RuntimeError(
                "AI modification response must be an object"
            )

        if "changes" not in result:
            raise RuntimeError(
                "AI modification response missing changes"
            )

        if not isinstance(result["changes"], list):
            raise RuntimeError(
                "changes must be a list"
            )

        existing_paths = {
            file.get("path")
            for file in context.get("files", [])
            if file.get("path")
        }

        planned_modify_paths = {
            item.get("file_path")
            for item in plan.get("files_to_modify", [])
            if item.get("file_path")
        }

        planned_create_paths = {
            item.get("file_path")
            for item in plan.get("files_to_create", [])
            if item.get("file_path")
        }

        allowed_modify_paths = (
            existing_paths
            & planned_modify_paths
        )

        allowed_create_paths = planned_create_paths

        for change in result["changes"]:

            if not isinstance(change, dict):
                raise RuntimeError(
                    "Each change must be an object"
                )

            required_fields = {
                "file_path",
                "action",
                "content",
            }

            missing = required_fields - change.keys()

            if missing:
                raise RuntimeError(
                    f"Change missing fields: {sorted(missing)}"
                )

            file_path = change["file_path"]
            action = change["action"]
            content = change["content"]

            if not isinstance(file_path, str):
                raise RuntimeError(
                    "file_path must be a string"
                )

            if action not in {
                "modify",
                "create",
            }:
                raise RuntimeError(
                    f"Unsupported file action: {action}"
                )

            if not isinstance(content, str):
                raise RuntimeError(
                    f"Content must be a string for {file_path}"
                )

            normalized_path = os.path.normpath(
                file_path
            )

            if (
                normalized_path.startswith("..")
                or os.path.isabs(normalized_path)
            ):
                raise RuntimeError(
                    f"Unsafe file path returned by AI: {file_path}"
                )

            normalized_path = normalized_path.replace(
                "\\",
                "/",
            )

            if action == "modify":

                if file_path not in allowed_modify_paths:
                    raise RuntimeError(
                        f"Unauthorized modification: {file_path}"
                    )

            elif action == "create":

                if file_path not in allowed_create_paths:
                    raise RuntimeError(
                        f"Unauthorized file creation: {file_path}"
                    )

    @staticmethod
    def apply_changes(
        repository_path: str,
        changes: dict,
    ) -> list:

        applied_files = []

        for change in changes.get("changes", []):

            file_path = change.get("file_path")
            action = change.get("action")
            content = change.get("content")

            if not file_path:
                raise RuntimeError(
                    "AI returned a change without a file path"
                )

            if action not in {
                "modify",
                "create",
            }:
                raise RuntimeError(
                    f"Unsupported file action: {action}"
                )

            if not isinstance(content, str):
                raise RuntimeError(
                    f"AI returned invalid content for {file_path}"
                )

            normalized_path = os.path.normpath(
                file_path
            )

            if (
                normalized_path.startswith("..")
                or os.path.isabs(normalized_path)
            ):
                raise RuntimeError(
                    f"Unsafe file path returned by AI: {file_path}"
                )

            file_path_on_disk = os.path.join(
                repository_path,
                normalized_path,
            )

            repository_root = os.path.abspath(
                repository_path
            )

            absolute_file_path = os.path.abspath(
                file_path_on_disk
            )

            if not absolute_file_path.startswith(
                repository_root + os.sep
            ):
                raise RuntimeError(
                    f"Unsafe file path returned by AI: {file_path}"
                )

            if action == "modify":

                if not os.path.isfile(
                    absolute_file_path
                ):
                    raise RuntimeError(
                        f"File does not exist: {file_path}"
                    )

            elif action == "create":

                if os.path.exists(
                    absolute_file_path
                ):
                    raise RuntimeError(
                        f"File already exists: {file_path}"
                    )

                parent_directory = os.path.dirname(
                    absolute_file_path
                )

                if parent_directory:
                    os.makedirs(
                        parent_directory,
                        exist_ok=True,
                    )

            with open(
                absolute_file_path,
                "w",
                encoding="utf-8",
            ) as file:
                file.write(content)

            applied_files.append(
                normalized_path.replace(
                    "\\",
                    "/",
                )
            )

        return applied_files