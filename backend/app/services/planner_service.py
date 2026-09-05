import json

from app.services.ai_service import AIService


class PlannerService:

    @classmethod
    def create_plan(
        cls,
        change_request: str,
        context: dict,
    ) -> dict:

        prompt = f"""
You are Syntra, an autonomous AI software engineering agent.

The user wants to modify an existing software repository.

Your task is to create a precise implementation plan.

USER REQUEST:
{change_request}

REPOSITORY CONTEXT:
{json.dumps(context, indent=2)}

Analyze the request against the repository.

Determine:
1. What the user wants
2. Which files are likely relevant
3. What changes should be made
4. What tests need to be added or modified
5. What validation should be performed
6. Potential risks or compatibility concerns

Return ONLY valid JSON in exactly this structure:

{{
  "summary": "short description of the requested change",
  "files_to_modify": [
    {{
      "path": "relative/file/path",
      "reason": "why this file needs modification"
    }}
  ],
  "files_to_create": [
    {{
      "path": "relative/file/path",
      "reason": "why this file should be created"
    }}
  ],
  "tests_to_modify": [
    {{
      "path": "relative/test/path",
      "reason": "what should be tested"
    }}
  ],
  "implementation_steps": [
    "step 1",
    "step 2"
  ],
  "validation_steps": [
    "validation 1",
    "validation 2"
  ],
  "risks": [
    "risk 1"
  ]
}}

Do not write or modify code.
Do not include markdown.
Return JSON only.
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
                    "AI returned an invalid planning response"
                )