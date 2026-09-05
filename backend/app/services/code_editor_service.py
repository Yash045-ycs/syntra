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
            item["path"]
            for item in plan.get("files_to_modify", [])
        }

        relevant_files.update(
            item["path"]
            for item in plan.get("tests_to_modify", [])
        )

        files = [
            file
            for file in context.get("files", [])
            if file["path"] in relevant_files
        ]

        prompt = f"""
You are Syntra, an autonomous AI software engineering agent.

Modify the existing repository according to the user's request.

USER REQUEST:
{change_request}

IMPLEMENTATION PLAN:
{json.dumps(plan, indent=2)}

RELEVANT EXISTING FILES:
{json.dumps(files, indent=2)}

FILES TO CREATE:
{json.dumps(plan.get("files_to_create", []), indent=2)}

Generate the required file changes.

Rules:

1. Existing files may use action "modify".
2. New files listed in FILES TO CREATE may use action "create".
3. Never create a file unless it is listed in FILES TO CREATE.
4. Every modified file must exactly match a path from RELEVANT EXISTING FILES.
5. Every created file must exactly match a path from FILES TO CREATE.
6. Preserve existing functionality unless the request requires changing it.
7. Do not remove unrelated code.
8. Preserve the project's existing coding style.
9. Update tests when required.
10. Return complete file contents.
11. Do not return markdown.
12. Do not use code fences.
13. Return ONLY valid JSON.

Return exactly:

{{
  "changes": [
    {{
      "path": "relative/file/path",
      "action": "modify",
      "content": "complete updated file content"
    }},
    {{
      "path": "relative/new/file/path",
      "action": "create",
      "content": "complete new file content"
    }}
  ]
}}
"""

        response = AIService.ask(prompt)

        try:
            return json.loads(response)

        except json.JSONDecodeError:

            cleaned = response.strip()

            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]

            if cleaned.startswith("```"):
                cleaned = cleaned[3:]

            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            try:
                return json.loads(cleaned.strip())

            except json.JSONDecodeError:
                raise RuntimeError(
                    "AI returned an invalid code modification response"
                )

    @staticmethod
    def apply_changes(
        repository_path: str,
        changes: dict,
    ) -> list:

        applied_files = []

        for change in changes.get("changes", []):

            path = change.get("path")
            action = change.get("action")
            content = change.get("content")

            if not path:
                raise RuntimeError(
                    "AI returned a change without a file path"
                )

            if action not in {"modify", "create"}:
                raise RuntimeError(
                    f"Unsupported file action: {action}"
                )

            if content is None:
                raise RuntimeError(
                    f"AI returned empty content for {path}"
                )

            normalized_path = os.path.normpath(path)

            if (
                normalized_path.startswith("..")
                or os.path.isabs(normalized_path)
            ):
                raise RuntimeError(
                    f"Unsafe file path returned by AI: {path}"
                )

            file_path = os.path.join(
                repository_path,
                normalized_path,
            )

            repository_root = os.path.abspath(
                repository_path
            )

            absolute_file_path = os.path.abspath(
                file_path
            )

            if not absolute_file_path.startswith(
                repository_root + os.sep
            ):
                raise RuntimeError(
                    f"Unsafe file path returned by AI: {path}"
                )

            if action == "modify":

                if not os.path.isfile(
                    absolute_file_path
                ):
                    raise RuntimeError(
                        f"File does not exist: {path}"
                    )

            elif action == "create":

                if os.path.exists(
                    absolute_file_path
                ):
                    raise RuntimeError(
                        f"File already exists: {path}"
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
                normalized_path.replace("\\", "/")
            )

        return applied_files