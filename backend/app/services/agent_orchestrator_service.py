import re
import subprocess
from datetime import datetime
from pathlib import Path
import traceback

from app.services.code_retrieval_service import CodeRetrievalService
from app.services.code_planner_service import CodePlannerService
from app.services.code_modifier_service import CodeModifierService
from app.services.code_repair_service import CodeRepairService
from app.services.code_change_applier_service import CodeChangeApplierService
from app.services.diff_security_service import DiffSecurityService
from app.services.test_runner_service import TestRunnerService
from app.services.git_service import GitService
from app.services.github_service import GitHubService
from app.services.activity_log_service import ActivityLogService


class AgentOrchestratorService:

    MAX_REPAIR_ITERATIONS = 3

    @classmethod
    def run(
        cls,
        db,
        repository_path: str,
        project_id: int,
        user_id: int,
        agent_run_id: int,
        repository_url: str,
        commit_sha: str,
        user_request: str,
        access_token: str,
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

        if not access_token:
            raise ValueError(
                "GitHub access token is required"
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

        ActivityLogService.log(
            db=db,
            project_id=project_id,
            user_id=user_id,
            agent_run_id=agent_run_id,
            event_type="repository_analyzed",
            message=f"Syntra is analyzing the repository on branch {base_branch}.",
        )

        repository_files = cls._get_repository_files(
            repository
        )

        ActivityLogService.log(
            db=db,
            project_id=project_id,
            user_id=user_id,
            agent_run_id=agent_run_id,
            event_type="repository_inventory_created",
            message=(
                f"Syntra discovered {len(repository_files)} "
                "repository file(s)."
            ),
        )

        retrieved_chunks = CodeRetrievalService.search(
            db=db,
            query=user_request,
            project_id=project_id,
            user_id=user_id,
            commit_sha=commit_sha,
            top_k=8,
        )

        ActivityLogService.log(
            db=db,
            project_id=project_id,
            user_id=user_id,
            agent_run_id=agent_run_id,
            event_type="code_retrieved",
            message=(
                f"Syntra retrieved {len(retrieved_chunks)} "
                "relevant code context chunks."
            ),
        )

        try:
            plan = CodePlannerService.create_plan(
                user_request=user_request,
                retrieved_chunks=retrieved_chunks,
                repository_files=repository_files,
            )
        except Exception as exc:
            print("\n" + "=" * 80)
            print("SYNTRA PLANNER ERROR")
            print("=" * 80)
            print(f"ERROR TYPE: {type(exc).__name__}")
            print(f"ERROR: {exc}")
            print("\nFULL TRACEBACK:")
            traceback.print_exc()
            print("=" * 80 + "\n")
            raise

        planned_files = cls._get_planned_files(
            plan
        )

        files_to_create = cls._get_files_to_create(
            plan
        )

        all_planned_files = list(
            dict.fromkeys(
                planned_files + files_to_create
            )
        )

        ActivityLogService.log(
            db=db,
            project_id=project_id,
            user_id=user_id,
            agent_run_id=agent_run_id,
            event_type="plan_created",
            message=(
                f"Syntra created a code modification plan "
                f"for {len(planned_files)} existing file(s) "
                f"and {len(files_to_create)} new file(s)."
            ),
        )

        if not all_planned_files:
            ActivityLogService.log(
                db=db,
                project_id=project_id,
                user_id=user_id,
                agent_run_id=agent_run_id,
                event_type="no_changes_required",
                message="Syntra determined that no file changes are required.",
            )

            return {
                "status": "no_changes_required",
                "base_branch": base_branch,
                "branch": base_branch,
                "retrieved_chunks": retrieved_chunks,
                "repository_files": repository_files,
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

        ActivityLogService.log(
            db=db,
            project_id=project_id,
            user_id=user_id,
            agent_run_id=agent_run_id,
            event_type="branch_created",
            message=f"Syntra created branch {branch_name}.",
        )

        applied_backups = []

        try:
            source_files = cls._read_source_files(
                repository,
                planned_files,
            )

            ActivityLogService.log(
                db=db,
                project_id=project_id,
                user_id=user_id,
                agent_run_id=agent_run_id,
                event_type="source_files_loaded",
                message=(
                    f"Syntra loaded {len(source_files)} "
                    "existing source file(s) for modification."
                ),
            )

            modification = CodeModifierService.generate_changes(
                user_request=user_request,
                plan=plan,
                source_files=source_files,
            )

            changes = modification["changes"]

            ActivityLogService.log(
                db=db,
                project_id=project_id,
                user_id=user_id,
                agent_run_id=agent_run_id,
                event_type="code_changes_generated",
                message=(
                    f"Syntra generated changes for "
                    f"{len(changes)} file(s)."
                ),
            )

            if not changes:
                cls._restore_branch(
                    repository,
                    base_branch,
                )

                ActivityLogService.log(
                    db=db,
                    project_id=project_id,
                    user_id=user_id,
                    agent_run_id=agent_run_id,
                    event_type="no_changes_generated",
                    message=(
                        "Syntra generated no applicable code changes."
                    ),
                )

                return {
                    "status": "no_changes_generated",
                    "base_branch": base_branch,
                    "branch": base_branch,
                    "retrieved_chunks": retrieved_chunks,
                    "repository_files": repository_files,
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

            planned_change_files = list(
                dict.fromkeys(
                    change["file_path"]
                    for change in changes
                    if isinstance(change, dict)
                    and isinstance(
                        change.get("file_path"),
                        str,
                    )
                )
            )

            ActivityLogService.log(
                db=db,
                project_id=project_id,
                user_id=user_id,
                agent_run_id=agent_run_id,
                event_type="changes_applied",
                message=(
                    f"Syntra applied changes to "
                    f"{len(planned_change_files)} file(s)."
                ),
            )

            validation = DiffSecurityService.validate(
                repository_path=str(repository),
                planned_files=planned_change_files,
            )

            print("\n" + "=" * 80)
            print("SYNTRA DIFF SECURITY VALIDATION")
            print("=" * 80)
            print("PLANNED FILES:", planned_change_files)
            print("CHANGED FILES:", validation.get("changed_files"))
            print("UNEXPECTED FILES:", validation.get("unexpected_files"))
            print("PROTECTED FILES:", validation.get("protected_files"))
            print("SECRET MATCHES:", validation.get("secret_matches"))
            print("CHANGED LINES:", validation.get("changed_lines"))
            print("ERRORS:", validation.get("errors"))
            print("SAFE:", validation.get("safe"))
            print("=" * 80 + "\n")

            if not validation["safe"]:
                ActivityLogService.log(
                    db=db,
                    project_id=project_id,
                    user_id=user_id,
                    agent_run_id=agent_run_id,
                    event_type="security_validation_failed",
                    message="Syntra security validation failed for the generated changes.",
                )

                raise RuntimeError(
                    f"Security validation failed: "
                    f"{validation['errors']}"
                )

            ActivityLogService.log(
                db=db,
                project_id=project_id,
                user_id=user_id,
                agent_run_id=agent_run_id,
                event_type="security_validation_passed",
                message="Syntra security validation passed.",
            )

            test_result = TestRunnerService.run(
                repository_path=str(repository),
            )

            if test_result["executed"]:
                if test_result["passed"]:
                    ActivityLogService.log(
                        db=db,
                        project_id=project_id,
                        user_id=user_id,
                        agent_run_id=agent_run_id,
                        event_type="tests_passed",
                        message="Automated tests passed successfully.",
                    )
                else:
                    ActivityLogService.log(
                        db=db,
                        project_id=project_id,
                        user_id=user_id,
                        agent_run_id=agent_run_id,
                        event_type="tests_failed",
                        message="Automated tests failed. Syntra will attempt repairs.",
                    )
            else:
                ActivityLogService.log(
                    db=db,
                    project_id=project_id,
                    user_id=user_id,
                    agent_run_id=agent_run_id,
                    event_type="tests_not_run",
                    message="No automated test suite was detected or executed.",
                )

            repair_iterations = 0
            repair_history = []

            while (
                test_result["executed"]
                and not test_result["passed"]
                and repair_iterations < cls.MAX_REPAIR_ITERATIONS
            ):
                repair_iterations += 1

                ActivityLogService.log(
                    db=db,
                    project_id=project_id,
                    user_id=user_id,
                    agent_run_id=agent_run_id,
                    event_type="repair_started",
                    message=(
                        f"Syntra started repair iteration "
                        f"{repair_iterations} of "
                        f"{cls.MAX_REPAIR_ITERATIONS}."
                    ),
                )

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
                    ActivityLogService.log(
                        db=db,
                        project_id=project_id,
                        user_id=user_id,
                        agent_run_id=agent_run_id,
                        event_type="repair_no_changes",
                        message=(
                            f"Syntra could not generate changes "
                            f"for repair iteration {repair_iterations}."
                        ),
                    )
                    break

                repair_applied = (
                    CodeChangeApplierService.apply_changes(
                        repository_path=str(repository),
                        changes=repair_changes,
                    )
                )

                applied_backups.append(repair_applied)

                ActivityLogService.log(
                    db=db,
                    project_id=project_id,
                    user_id=user_id,
                    agent_run_id=agent_run_id,
                    event_type="repair_applied",
                    message=(
                        f"Syntra applied repair changes "
                        f"for iteration {repair_iterations}."
                    ),
                )

                repair_validation = DiffSecurityService.validate(
                    repository_path=str(repository),
                    planned_files=planned_change_files,
                )

                if not repair_validation["safe"]:
                    ActivityLogService.log(
                        db=db,
                        project_id=project_id,
                        user_id=user_id,
                        agent_run_id=agent_run_id,
                        event_type="repair_security_validation_failed",
                        message=(
                            f"Security validation failed during "
                            f"repair iteration {repair_iterations}."
                        ),
                    )

                    raise RuntimeError(
                        "Repair security validation failed: "
                        f"{repair_validation['errors']}"
                    )

                test_result = TestRunnerService.run(
                    repository_path=str(repository),
                )

                if test_result["passed"]:
                    ActivityLogService.log(
                        db=db,
                        project_id=project_id,
                        user_id=user_id,
                        agent_run_id=agent_run_id,
                        event_type="repair_tests_passed",
                        message=(
                            f"Tests passed after repair iteration "
                            f"{repair_iterations}."
                        ),
                    )
                else:
                    ActivityLogService.log(
                        db=db,
                        project_id=project_id,
                        user_id=user_id,
                        agent_run_id=agent_run_id,
                        event_type="repair_tests_failed",
                        message=(
                            f"Tests still failed after repair iteration "
                            f"{repair_iterations}."
                        ),
                    )

            if test_result["executed"] and test_result["passed"]:
                status = "success"
            elif test_result["executed"]:
                status = "tests_failed"
            else:
                status = "no_tests"

            if status == "tests_failed":
                raise RuntimeError(
                    "Syntra validation did not succeed: tests_failed"
                )

            final_validation = DiffSecurityService.validate(
                repository_path=str(repository),
                planned_files=planned_change_files,
            )

            if not final_validation["safe"]:
                ActivityLogService.log(
                    db=db,
                    project_id=project_id,
                    user_id=user_id,
                    agent_run_id=agent_run_id,
                    event_type="final_security_validation_failed",
                    message="Final security validation failed.",
                )

                raise RuntimeError(
                    "Final security validation failed: "
                    f"{final_validation['errors']}"
                )

            ActivityLogService.log(
                db=db,
                project_id=project_id,
                user_id=user_id,
                agent_run_id=agent_run_id,
                event_type="final_validation_passed",
                message="Final security validation passed.",
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

            ActivityLogService.log(
                db=db,
                project_id=project_id,
                user_id=user_id,
                agent_run_id=agent_run_id,
                event_type="commit_created",
                message=f"Syntra created commit on branch {branch_name}.",
            )

            print(
                "[Agent] Pushing Syntra branch using GitHub OAuth"
            )

            push_result = GitService.push_branch(
                repository_path=str(repository),
                branch_name=branch_name,
                access_token=access_token,
            )

            if not push_result["success"]:
                raise RuntimeError(
                    f"GitHub push failed: "
                    f"{push_result['stderr']}"
                )

            print(
                "[Agent] GitHub push completed"
            )

            ActivityLogService.log(
                db=db,
                project_id=project_id,
                user_id=user_id,
                agent_run_id=agent_run_id,
                event_type="branch_pushed",
                message=f"Syntra pushed branch {branch_name} to GitHub.",
            )

            repository_info = cls._get_repository_info(
                repository_url=repository_url,
                access_token=access_token,
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
                access_token=access_token,
            )

            print(
                "[Agent] GitHub Pull Request created"
            )

            ActivityLogService.log(
                db=db,
                project_id=project_id,
                user_id=user_id,
                agent_run_id=agent_run_id,
                event_type="pull_request_created",
                message=(
                    f"Syntra created pull request "
                    f"#{pull_request.get('number')}."
                ),
            )

            for backup in applied_backups:
                CodeChangeApplierService.cleanup_backups(
                    backup["backup_directory"]
                )

            ActivityLogService.log(
                db=db,
                project_id=project_id,
                user_id=user_id,
                agent_run_id=agent_run_id,
                event_type="agent_processing_completed",
                message="Syntra completed code generation, validation, commit, push, and pull request creation.",
            )

            return {
                "status": "success",
                "base_branch": base_branch,
                "branch": branch_name,
                "retrieved_chunks": retrieved_chunks,
                "repository_files": repository_files,
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

        except Exception as exc:
            print("\n" + "=" * 80)
            print("SYNTRA AGENT ERROR")
            print("=" * 80)
            print(f"ERROR TYPE: {type(exc).__name__}")
            print(f"ERROR: {exc}")
            print("\nFULL TRACEBACK:")
            traceback.print_exc()
            print("=" * 80 + "\n")

            try:
                ActivityLogService.log(
                    db=db,
                    project_id=project_id,
                    user_id=user_id,
                    agent_run_id=agent_run_id,
                    event_type="agent_processing_failed",
                    message=f"Syntra agent processing failed: {str(exc)}",
                )
            except Exception:
                pass

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

        created_files = [
            item["file_path"]
            for item in plan.get("files_to_create", [])
            if isinstance(item, dict)
            and isinstance(item.get("file_path"), str)
        ]

        risks = plan.get("risks", [])
        validation_steps = plan.get("validation", [])

        files_text = "\n".join(
            f"- `{file_path}`"
            for file_path in modified_files
        )

        if created_files:
            files_text += "\n\n### Created Files\n\n"
            files_text += "\n".join(
                f"- `{file_path}`"
                for file_path in created_files
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
    def _get_repository_files(
        repository: Path,
    ) -> list[str]:

        files = []

        for path in repository.rglob("*"):
            if not path.is_file():
                continue

            try:
                relative_path = path.relative_to(
                    repository
                )
            except ValueError:
                continue

            parts = relative_path.parts

            if any(
                part in {
                    ".git",
                    ".venv",
                    "venv",
                    "node_modules",
                    "__pycache__",
                    ".pytest_cache",
                    ".mypy_cache",
                    ".ruff_cache",
                    ".idea",
                    ".vscode",
                }
                for part in parts
            ):
                continue

            files.append(
                relative_path.as_posix()
            )

        return sorted(
            set(files)
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
                    files.append(
                        file_path
                    )

        return list(
            dict.fromkeys(files)
        )

    @staticmethod
    def _get_files_to_create(
        plan: dict,
    ) -> list[str]:

        files = []

        for item in plan.get("files_to_create", []):
            if isinstance(item, dict):
                file_path = item.get("file_path")

                if isinstance(file_path, str):
                    files.append(
                        file_path
                    )

        return list(
            dict.fromkeys(files)
        )

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
                target.relative_to(
                    repository
                )
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