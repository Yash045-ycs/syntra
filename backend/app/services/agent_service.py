import json
import uuid

from app.db.models import User
from app.services.repository_service import RepositoryService
from app.services.scanner_service import ScannerService
from app.services.context_service import CodebaseContextService
from app.services.planner_service import PlannerService
from app.services.code_editor_service import CodeEditorService
from app.services.test_runner_service import TestRunnerService
from app.services.git_service import GitService
from app.services.github_service import GitHubService
from app.services.token_encryption_service import TokenEncryptionService
from app.services.ai_service import AIService
from app.services.github_app_service import GitHubAppService
from app.services.security_service import SecurityService
from app.services.diff_integrity_service import DiffIntegrityService


class AgentService:

    MAX_FIX_ATTEMPTS = 3

    @classmethod
    def execute(
        cls,
        repository_url: str,
        change_request: str,
        current_user: User,
    ) -> dict:

        repository_path = None

        if not current_user.github_access_token:
            raise RuntimeError(
                "GitHub account is not connected"
            )

        if not current_user.github_installation_id:
            raise RuntimeError(
                "GitHub App is not installed"
            )

        access_token = (
            GitHubAppService.generate_installation_token(
                current_user.github_installation_id
            )
        )

        branch_name = (
            "syntra/"
            + uuid.uuid4().hex[:8]
        )

        try:
            print("[Agent] Starting execution")

            repository_path = (
                RepositoryService.clone_repository(
                    repository_url,
                    access_token=access_token,
                )
            )

            print("[Agent] Repository cloned")

            branch_result = GitService.create_branch(
                repository_path,
                branch_name,
            )

            if not branch_result["success"]:
                raise RuntimeError(
                    "Failed to create Git branch: "
                    + branch_result["stderr"]
                )

            print(
                f"[Agent] Created branch: "
                f"{branch_name}"
            )

            analysis = ScannerService.scan_repository(
                repository_path
            )

            print("[Agent] Repository scanned")

            context = CodebaseContextService.build_context(
                repository_path,
                analysis,
            )

            print("[Agent] Context built")

            plan = PlannerService.create_plan(
                change_request,
                context,
            )

            print("[Agent] Plan created")

            changes = CodeEditorService.generate_changes(
                change_request,
                plan,
                context,
            )

            print("[Agent] Code changes generated")

            applied_files = list(
    CodeEditorService.apply_changes(
        repository_path,
        changes,
    )
)

            print(
                f"[Agent] Applied changes: "
                f"{applied_files}"
            )

            test_result = TestRunnerService.run_tests(
                repository_path,
                analysis,
            )

            attempts = 0
            fix_history = []

            while (
                not test_result["passed"]
                and attempts < cls.MAX_FIX_ATTEMPTS
            ):

                attempts += 1

                print(
                    f"[Agent] Tests failed. "
                    f"Starting fix attempt "
                    f"{attempts}/{cls.MAX_FIX_ATTEMPTS}"
                )

                fix = cls.generate_fix(
                    change_request=change_request,
                    plan=plan,
                    context=context,
                    changes=changes,
                    test_result=test_result,
                )

                fix_history.append(
                    {
                        "attempt": attempts,
                        "fix": fix,
                    }
                )

                fix_applied_files = CodeEditorService.apply_changes(
    repository_path,
    fix,
)

                for file_path in fix_applied_files:
                    if file_path not in applied_files:
                        applied_files.append(file_path)

                print(
                    f"[Agent] Fix {attempts} applied"
                )

                test_result = TestRunnerService.run_tests(
                    repository_path,
                    analysis,
                )

            if not test_result["passed"]:
                print(
                    "[Agent] Tests failed after "
                    f"{attempts} fix attempts"
                )

                return {
                    "success": False,
                    "repository_url": repository_url,
                    "change_request": change_request,
                    "branch_name": branch_name,
                    "plan": plan,
                    "initial_changes": changes,
                    "applied_files": applied_files,
                    "test_result": test_result,
                    "fix_attempts": attempts,
                    "fix_history": fix_history,
                    "git": None,
                    "github": None,
                }

            print("[Agent] Tests passed")

            allowed_files = list(
                {
                    change["path"]
                    for change in changes.get(
                        "changes",
                        [],
                    )
                }
            )

            for fix_item in fix_history:
                for change in fix_item["fix"].get(
                    "changes",
                    [],
                ):
                    if change["path"] not in allowed_files:
                        allowed_files.append(
                            change["path"]
                        )

            security_result = (
                SecurityService.validate_changed_files(
                    repository_path,
                    allowed_files,
                )
            )

            print(
                "[Agent] Security validation: "
                + security_result["reason"]
            )

            if not security_result["passed"]:
                return {
                    "success": False,
                    "repository_url": repository_url,
                    "change_request": change_request,
                    "branch_name": branch_name,
                    "plan": plan,
                    "initial_changes": changes,
                    "applied_files": applied_files,
                    "test_result": test_result,
                    "fix_attempts": attempts,
                    "fix_history": fix_history,
                    "security": security_result,
                    "git": None,
                    "github": None,
                }

            git_status = GitService.get_status(
                repository_path
            )

            if not git_status["success"]:
                raise RuntimeError(
                    "Failed to read Git status: "
                    + git_status["stderr"]
                )

            git_diff = GitService.get_diff(
    repository_path
)

            if not git_diff["success"]:
                raise RuntimeError(
                    "Failed to read Git diff: "
                    + git_diff["stderr"]
                )

            expected_files = list(
        dict.fromkeys(
            applied_files
        )
    )

            diff_integrity = DiffIntegrityService.validate(
                repository_path,
                expected_files,
            )

            print(
                "[Agent] Diff integrity: "
                + diff_integrity["reason"]
            )

            if not diff_integrity["passed"]:
                return {
                    "success": False,
                    "repository_url": repository_url,
                    "change_request": change_request,
                    "branch_name": branch_name,
                    "plan": plan,
                    "initial_changes": changes,
                    "applied_files": applied_files,
                    "test_result": test_result,
                    "fix_attempts": attempts,
                    "fix_history": fix_history,
                    "security": security_result,
                    "diff_integrity": diff_integrity,
                    "git": None,
                    "github": None,
                }

            commit_message = (
                "feat: "
                + change_request.strip()
            )

            commit_result = GitService.commit_changes(
                repository_path,
                commit_message,
            )

            if not commit_result["success"]:
                raise RuntimeError(
                    "Failed to commit changes: "
                    + commit_result["stderr"]
                )

            print("[Agent] Changes committed")

            github_repository = cls.get_github_repository(
                repository_url,
                access_token,
            )

            print(
                "[Agent] GitHub repository verified: "
                + github_repository["full_name"]
            )

            push_result = GitService.push_branch(
    repository_path,
    branch_name,
    access_token=access_token,
)

            if not push_result["success"]:
                raise RuntimeError(
                    "Failed to push branch: "
                    + push_result["stderr"]
                )

            print(
                f"[Agent] Branch pushed: "
                f"{branch_name}"
            )

            owner = github_repository["owner"]
            repository = github_repository["name"]
            default_branch = github_repository["default_branch"]

            pr_title = (
                "Syntra: "
                + change_request.strip()
            )

            pr_body = cls.build_pull_request_body(
                change_request=change_request,
                plan=plan,
                applied_files=applied_files,
                test_result=test_result,
                fix_attempts=attempts,
            )

            pull_request = GitHubService.create_pull_request(
                owner=owner,
                repository=repository,
                title=pr_title,
                body=pr_body,
                head=branch_name,
                base=default_branch,
                access_token=access_token,
            )

            print(
                f"[Agent] Pull request created: "
                f"{pull_request['url']}"
            )

            return {
                "success": True,
                "repository_url": repository_url,
                "change_request": change_request,
                "branch_name": branch_name,
                "plan": plan,
                "initial_changes": changes,
                "applied_files": applied_files,
                "test_result": test_result,
                "fix_attempts": attempts,
                "fix_history": fix_history,
                "security": security_result,
                "diff_integrity": diff_integrity,
                "git": {
                    "status": git_status,
                    "diff": git_diff,
                    "commit": commit_result,
                    "push": push_result,
                },
                "github": {
                    "repository": github_repository,
                    "pull_request": pull_request,
                },
            }

        finally:

            if repository_path:
                RepositoryService.cleanup_repository(
                    repository_path
                )

    @staticmethod
    def get_github_repository(
        repository_url: str,
        access_token: str,
    ) -> dict:

        parsed = repository_url.rstrip("/").split("/")

        if len(parsed) < 2:
            raise RuntimeError(
                "Invalid GitHub repository URL"
            )

        owner = parsed[-2]
        repository = parsed[-1]

        return GitHubService.get_repository(
            owner,
            repository,
            access_token=access_token,
        )

    @staticmethod
    def build_pull_request_body(
        change_request: str,
        plan: dict,
        applied_files: list,
        test_result: dict,
        fix_attempts: int,
    ) -> str:

        implementation_steps = "\n".join(
            f"- {step}"
            for step in plan.get(
                "implementation_steps",
                [],
            )
        )

        files = "\n".join(
            f"- `{file}`"
            for file in applied_files
        )

        return f"""## Syntra Automated Pull Request

### Change Request

{change_request}

### Summary

{plan.get("summary", "Automated code change generated by Syntra.")}

### Implementation

{implementation_steps}

### Modified Files

{files}

### Validation

- Tests passed: {test_result["passed"]}
- Exit code: {test_result["exit_code"]}
- Fix attempts: {fix_attempts}

This pull request was automatically generated by Syntra.
"""

    @classmethod
    def generate_fix(
        cls,
        change_request: str,
        plan: dict,
        context: dict,
        changes: dict,
        test_result: dict,
    ) -> dict:

        prompt = f"""
You are Syntra, an autonomous AI software engineering agent.

You previously modified a repository according to a user request.

The tests are now failing.

Your task is to diagnose the failure and generate the smallest
possible code changes required to fix it.

USER REQUEST:
{change_request}

IMPLEMENTATION PLAN:
{json.dumps(plan, indent=2)}

PREVIOUS CHANGES:
{json.dumps(changes, indent=2)}

TEST RESULT:
{json.dumps(test_result, indent=2)}

REPOSITORY CONTEXT:
{json.dumps(context, indent=2)}

Rules:

1. Fix the actual test failure.
2. Preserve the requested functionality.
3. Do not introduce unrelated changes.
4. Only modify files that already exist in the repository.
5. Return complete file contents.
6. Do not return markdown.
7. Do not use code fences.
8. Return ONLY valid JSON.

Return exactly:

{
  "changes": [
    {
      "path": "relative/file/path",
      "action": "modify",
      "content": "complete updated file content"
    }
  ]
}
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
                    "AI returned an invalid fix response"
                )