import re
import subprocess
from datetime import datetime
from pathlib import Path

from app.services.code_retrieval_service import CodeRetrievalService
from app.services.code_planner_service import CodePlannerService
from app.services.code_modifier_service import CodeModifierService
from app.services.code_repair_service import CodeRepairService
from app.services.code_change_applier_service import CodeChangeApplierService
from app.services.diff_security_service import DiffSecurityService
from app.services.test_runner_service import TestRunnerService
from app.services.git_service import GitService
from app.services.github_service import GitHubService


class AgentOrchestratorService:

    MAX_REPAIR_ITERATIONS = 3

    @classmethod
    def run(
        cls,
        db,
        repository_path: str,
        project_id: int,
        user_id: int,
        repository_url: str,
        commit_sha: str,
        user_request: str,
        installation_id: int,
    ) -> dict:

        repository = Path(repository_path).resolve()

        if not repository.exists():
            raise ValueError(
                f"Repository does not exist: {repository}"
            )

        if not user_request.strip():
            raise ValueError(
                "User request cannot be empty"
            )

        if installation_id <= 0:
            raise ValueError(
                "Valid GitHub installation ID is required"
            )

        cls._ensure_clean_repository(repository)

        current_branch_result = GitService.get_current_branch(
            str(repository)
        )

        if not current_branch_result["success"]:
            raise RuntimeError(
                f"Unable to determine current branch: "
                f"{current_branch_result['stderr']}"
            )

        base_branch = current_branch_result["stdout"]

        retrieved_chunks = CodeRetrievalService.search(
            db=db,
            query=user_request,
            project_id=project_id,
            user_id=user_id,
            commit_sha=commit_sha,
            top_k=8,
        )

        plan = CodePlannerService.create_plan(
            user_request=user_request,
            retrieved_chunks=retrieved_chunks,
        )

        planned_files = cls._get_planned_files(plan)

        if plan.get("files_to_create"):
            raise RuntimeError(
                "File creation is not supported by the current MVP."
            )

        if not planned_files:
            return {
                "status": "no_changes_required",
                "base_branch": base_branch,
                "branch": base_branch,
                "retrieved_chunks": retrieved_chunks,
                "plan": plan,
                "changes": [],
                "validation": None,
                "repair_iterations": 0,
            }

        branch_name = cls._generate_branch_name(
            user_request
        )

        branch_result = GitService.create_branch(
            repository_path=str(repository),
            branch_name=branch_name,
        )

        if not branch_result["success"]:
            raise RuntimeError(
                f"Unable to create Syntra branch: "
                f"{branch_result['stderr']}"
            )

        applied_backups = []

        try:
            source_files = cls._read_source_files(
                repository,
                planned_files,
            )

            modification = CodeModifierService.generate_changes(
                user_request=user_request,
                plan=plan,
                source_files=source_files,
            )

            changes = modification["changes"]

            if not changes:
                cls._restore_branch(
                    repository,
                    base_branch,
                )

                return {
                    "status": "no_changes_generated",
                    "base_branch": base_branch,
                    "branch": base_branch,
                    "retrieved_chunks": retrieved_chunks,
                    "plan": plan,
                    "modification": modification,
                    "validation": None,
                    "repair_iterations": 0,
                }

            applied = CodeChangeApplierService.apply_changes(
                repository_path=str(repository),
                changes=changes,
            )

            applied_backups.append(applied)

            planned_change_files = [
                change["file_path"]
                for change in changes
            ]

            validation = DiffSecurityService.validate(
                repository_path=str(repository),
                planned_files=planned_change_files,
            )

            if not validation["safe"]:
                raise RuntimeError(
                    f"Security validation failed: "
                    f"{validation['errors']}"
                )

            test_result = TestRunnerService.run(
                repository_path=str(repository),
            )

            repair_iterations = 0
            repair_history = []

            while (
                test_result["executed"]
                and not test_result["passed"]
                and repair_iterations < cls.MAX_REPAIR_ITERATIONS
            ):

                repair_iterations += 1

                current_source_files = cls._read_source_files(
                    repository,
                    planned_files,
                )

                repair = CodeRepairService.generate_repair(
                    user_request=user_request,
                    plan=plan,
                    failure_output=(
                        test_result["stdout"]
                        + "\n"
                        + test_result["stderr"]
                    ),
                    source_files=current_source_files,
                )

                repair_history.append(repair)

                repair_changes = repair["changes"]

                if not repair_changes:
                    break

                repair_applied = (
                    CodeChangeApplierService.apply_changes(
                        repository_path=str(repository),
                        changes=repair_changes,
                    )
                )

                applied_backups.append(repair_applied)

                repair_validation = DiffSecurityService.validate(
                    repository_path=str(repository),
                    planned_files=planned_change_files,
                )

                if not repair_validation["safe"]:
                    raise RuntimeError(
                        "Repair security validation failed: "
                        f"{repair_validation['errors']}"
                    )

                test_result = TestRunnerService.run(
                    repository_path=str(repository),
                )

            if test_result["executed"] and test_result["passed"]:
                status = "success"
            elif test_result["executed"]:
                status = "tests_failed"
            else:
                status = "validation_unavailable"

            if status != "success":
                raise RuntimeError(
                    f"Syntra validation did not succeed: {status}"
                )

            final_validation = DiffSecurityService.validate(
                repository_path=str(repository),
                planned_files=planned_change_files,
            )

            if not final_validation["safe"]:
                raise RuntimeError(
                    "Final security validation failed: "
                    f"{final_validation['errors']}"
                )

            commit_result = GitService.commit_changes(
                repository_path=str(repository),
                message=cls._generate_commit_message(
                    user_request
                ),
                file_paths=planned_change_files,
            )

            if not commit_result["success"]:
                raise RuntimeError(
                    f"Git commit failed: "
                    f"{commit_result['stderr']}"
                )

            print(
                "[Agent] Generating GitHub App installation token"
            )

            github_token = (
                GitHubService.create_installation_token(
                    installation_id
                )
            )

            if not github_token:
                raise RuntimeError(
                    "Unable to generate GitHub installation token"
                )

            print(
                "[Agent] Pushing Syntra branch to GitHub"
            )

            push_result = GitService.push_branch(
                repository_path=str(repository),
                branch_name=branch_name,
                access_token=github_token,
            )

            if not push_result["success"]:
                raise RuntimeError(
                    f"GitHub push failed: "
                    f"{push_result['stderr']}"
                )

            print(
                "[Agent] GitHub push completed"
            )

            repository_info = cls._get_repository_info(
                repository_url=repository_url,
                access_token=github_token,
            )

            print(
                "[Agent] Creating GitHub Pull Request"
            )

            pull_request = GitHubService.create_pull_request(
                owner=repository_info["owner"],
                repository=repository_info["repository"],
                title=cls._generate_pr_title(
                    user_request
                ),
                body=cls._generate_pr_body(
                    user_request=user_request,
                    plan=plan,
                    validation=final_validation,
                    test_result=test_result,
                    repair_iterations=repair_iterations,
                ),
                head=branch_name,
                base=base_branch,
                access_token=github_token,
            )

            print(
                "[Agent] GitHub Pull Request created"
            )

            for backup in applied_backups:
                CodeChangeApplierService.cleanup_backups(
                    backup["backup_directory"]
                )

            return {
                "status": "success",
                "base_branch": base_branch,
                "branch": branch_name,
                "retrieved_chunks": retrieved_chunks,
                "plan": plan,
                "modification": modification,
                "validation": final_validation,
                "test_result": test_result,
                "repair_iterations": repair_iterations,
                "repair_history": repair_history,
                "commit": commit_result,
                "push": push_result,
                "pull_request": pull_request,
            }

        except Exception:
            cls._rollback(
                repository_path=str(repository),
                applied_backups=applied_backups,
            )

            try:
                cls._restore_branch(
                    repository,
                    base_branch,
                )
            except Exception:
                pass

            raise

    @staticmethod
    def _get_repository_info(
        repository_url: str,
        access_token: str,
    ) -> dict:

        match = re.match(
            r"^https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$",
            repository_url.strip(),
        )

        if not match:
            raise ValueError(
                "Invalid GitHub repository URL"
            )

        owner = match.group(1)
        repository = match.group(2)

        repository_info = GitHubService.get_repository(
            owner=owner,
            repository=repository,
            access_token=access_token,
        )

        return {
            "owner": repository_info["owner"],
            "repository": repository_info["name"],
        }

    @staticmethod
    def _generate_pr_title(
        user_request: str,
    ) -> str:

        normalized = " ".join(
            user_request.strip().split()
        )

        if len(normalized) > 72:
            normalized = normalized[:69].rstrip() + "..."

        return f"Syntra: {normalized}"

    @staticmethod
    def _generate_pr_body(
        user_request: str,
        plan: dict,
        validation: dict,
        test_result: dict,
        repair_iterations: int,
    ) -> str:

        modified_files = [
            item["file_path"]
            for item in plan.get("files_to_modify", [])
            if isinstance(item, dict)
            and isinstance(item.get("file_path"), str)
        ]

        risks = plan.get("risks", [])
        validation_steps = plan.get("validation", [])

        files_text = "\n".join(
            f"- `{file_path}`"
            for file_path in modified_files
        )

        risks_text = "\n".join(
            f"- {risk}"
            for risk in risks
        ) or "- None identified"

        validation_text = "\n".join(
            f"- {step}"
            for step in validation_steps
        ) or "- Automated test validation completed"

        return f"""## Syntra AI Change

### Request

{user_request}

### Modified Files

{files_text}

### Validation

- Security validation: passed
- Automated tests: passed
- Changed lines: {validation["changed_lines"]}
- Repair iterations: {repair_iterations}

### Test Result

- Framework: {test_result.get("framework")}
- Command: `{test_result.get("command")}`
- Return code: {test_result.get("return_code")}

### Planned Validation

{validation_text}

### Identified Risks

{risks_text}

### Review

This pull request was generated by Syntra.

Please review the generated diff before merging.
"""

    @staticmethod
    def _ensure_clean_repository(
        repository: Path,
    ) -> None:

        result = subprocess.run(
            [
                "git",
                "-C",
                str(repository),
                "status",
                "--porcelain",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Unable to inspect Git status: "
                f"{result.stderr.strip()}"
            )

        if result.stdout.strip():
            raise RuntimeError(
                "Repository must have a clean working tree "
                "before Syntra can modify it."
            )

    @staticmethod
    def _rollback(
        repository_path: str,
        applied_backups: list[dict],
    ) -> None:

        for applied in reversed(applied_backups):
            try:
                CodeChangeApplierService.restore_changes(
                    repository_path=repository_path,
                    backups=applied["backups"],
                )
            finally:
                CodeChangeApplierService.cleanup_backups(
                    applied["backup_directory"]
                )

    @staticmethod
    def _get_planned_files(
        plan: dict,
    ) -> list[str]:

        files = []

        for item in plan.get("files_to_modify", []):
            if isinstance(item, dict):
                file_path = item.get("file_path")

                if isinstance(file_path, str):
                    files.append(file_path)

        return list(dict.fromkeys(files))

    @staticmethod
    def _read_source_files(
        repository: Path,
        file_paths: list[str],
    ) -> dict[str, str]:

        source_files = {}

        for file_path in file_paths:

            target = (
                repository / file_path
            ).resolve()

            try:
                target.relative_to(repository)
            except ValueError as exc:
                raise ValueError(
                    f"Source file escapes repository: {file_path}"
                ) from exc

            if not target.exists():
                raise ValueError(
                    f"Source file does not exist: {file_path}"
                )

            if not target.is_file():
                raise ValueError(
                    f"Source path is not a file: {file_path}"
                )

            source_files[file_path] = target.read_text(
                encoding="utf-8",
                errors="strict",
            )

        return source_files

    @staticmethod
    def _generate_branch_name(
        user_request: str,
    ) -> str:

        normalized = user_request.lower().strip()

        normalized = re.sub(
            r"[^a-z0-9]+",
            "-",
            normalized,
        )

        normalized = normalized.strip("-")

        if not normalized:
            normalized = "change"

        normalized = normalized[:40].rstrip("-")

        timestamp = datetime.utcnow().strftime(
            "%Y%m%d-%H%M%S"
        )

        return f"syntra/{normalized}-{timestamp}"

    @staticmethod
    def _generate_commit_message(
        user_request: str,
    ) -> str:

        normalized = " ".join(
            user_request.strip().split()
        )

        if len(normalized) > 72:
            normalized = normalized[:69].rstrip() + "..."

        return f"syntra: {normalized}"

    @staticmethod
    def _restore_branch(
        repository: Path,
        branch_name: str,
    ) -> None:

        result = GitService.run_git(
            str(repository),
            ["checkout", branch_name],
        )

        if not result["success"]:
            raise RuntimeError(
                f"Unable to restore branch {branch_name}: "
                f"{result['stderr']}"
            )