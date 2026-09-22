from datetime import datetime

from app.db.database import SessionLocal
from app.db.models import AgentRun
from app.services.repository_service import RepositoryService
from app.services.code_indexer_service import CodeIndexerService
from app.services.agent_orchestrator_service import AgentOrchestratorService
from app.services.activity_log_service import ActivityLogService


class AgentRunService:

    @staticmethod
    def run(
        repository_url,
        access_token,
        project_id,
        user_id,
        user_request,
    ):
        repository = None
        db = SessionLocal()

        agent_run = AgentRun(
            project_id=project_id,
            user_id=user_id,
            status="running",
            user_request=user_request,
            repair_iterations=0,
        )

        db.add(agent_run)
        db.commit()
        db.refresh(agent_run)

        print(
            f"[Activity] Creating activity log for agent run {agent_run.id}"
        )

        ActivityLogService.log(
            db=db,
            project_id=project_id,
            user_id=user_id,
            agent_run_id=agent_run.id,
            event_type="agent_run_started",
            message=f"Syntra started an agent run for: {user_request}",
        )

        print(
            f"[Activity] Activity log created for agent run {agent_run.id}"
        )

        try:
            if not repository_url:
                raise ValueError("repository_url is required")

            if not access_token:
                raise ValueError("GitHub access token is required")

            if not project_id:
                raise ValueError("project_id is required")

            if not user_id:
                raise ValueError("user_id is required")

            if not user_request:
                raise ValueError("user_request is required")

            repository = RepositoryService.prepare_repository(
                repository_url=repository_url,
                access_token=access_token,
            )

            agent_run.base_branch = repository.get("default_branch")
            agent_run.base_commit_sha = repository.get("commit_sha")

            db.commit()

            ActivityLogService.log(
                db=db,
                project_id=project_id,
                user_id=user_id,
                agent_run_id=agent_run.id,
                event_type="repository_prepared",
                message="Repository prepared successfully.",
            )

            index_result = CodeIndexerService.index_repository(
                db=db,
                repository_path=repository["local_path"],
                project_id=project_id,
                user_id=user_id,
                repository_url=repository_url,
                commit_sha=repository["commit_sha"],
            )

            ActivityLogService.log(
                db=db,
                project_id=project_id,
                user_id=user_id,
                agent_run_id=agent_run.id,
                event_type="repository_indexed",
                message="Repository indexing completed.",
            )

            result = AgentOrchestratorService.run(
                db=db,
                repository_path=repository["local_path"],
                project_id=project_id,
                user_id=user_id,
                agent_run_id=agent_run.id,
                repository_url=repository_url,
                commit_sha=repository["commit_sha"],
                user_request=user_request,
                access_token=access_token,
            )

            commit_result = result.get("commit") or {}
            pull_request = result.get("pull_request") or {}
            validation = result.get("validation") or {}
            test_result = result.get("test_result") or {}
            plan = result.get("plan") or {}

            agent_run.status = "completed"

            agent_run.agent_branch = result.get("branch")

            agent_run.agent_commit_sha = (
                AgentRunService._get_commit_sha(
                    commit_result
                )
            )

            agent_run.pr_number = pull_request.get("number")
            agent_run.pr_url = pull_request.get("url")
            agent_run.goal = plan.get("goal")

            if validation.get("safe") is True:
                agent_run.validation_status = "passed"
            else:
                agent_run.validation_status = "failed"

            if test_result.get("executed") is True:
                if test_result.get("passed") is True:
                    agent_run.test_status = "passed"
                else:
                    agent_run.test_status = "failed"
            else:
                agent_run.test_status = "not_run"

            agent_run.repair_iterations = result.get(
                "repair_iterations",
                0,
            )

            agent_run.completed_at = datetime.utcnow()

            db.commit()
            db.refresh(agent_run)

            ActivityLogService.log(
                db=db,
                project_id=project_id,
                user_id=user_id,
                agent_run_id=agent_run.id,
                event_type="agent_run_completed",
                message="Syntra completed the agent run successfully.",
            )

            return {
                "run_id": agent_run.id,
                "status": agent_run.status,
                "index_result": index_result,
                "agent_result": result,
            }

        except Exception as exc:
            db.rollback()

            agent_run.status = "failed"
            agent_run.error = str(exc)
            agent_run.completed_at = datetime.utcnow()

            db.add(agent_run)
            db.commit()
            db.refresh(agent_run)

            try:
                ActivityLogService.log(
                    db=db,
                    project_id=project_id,
                    user_id=user_id,
                    agent_run_id=agent_run.id,
                    event_type="agent_run_failed",
                    message=f"Syntra agent run failed: {exc}",
                )
            except Exception as activity_error:
                print(
                    f"[Activity] Failed to create failure log: "
                    f"{activity_error}"
                )

            raise

        finally:
            db.close()

            if repository:
                RepositoryService.cleanup_repository(
                    repository["local_path"]
                )

    @staticmethod
    def _get_commit_sha(commit_result: dict) -> str | None:
        stdout = commit_result.get("stdout", "")

        if not stdout:
            return None

        first_line = stdout.splitlines()[0].strip()

        if not first_line:
            return None

        parts = first_line.split()

        if len(parts) < 2:
            return None

        commit_sha = parts[1].strip("[]'\"")

        if len(commit_sha) < 7:
            return None

        return commit_sha