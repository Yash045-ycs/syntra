from datetime import datetime

from app.db.database import SessionLocal
from app.db.models import AgentRun
from app.services.repository_service import RepositoryService
from app.services.code_indexer_service import CodeIndexerService
from app.services.agent_orchestrator_service import AgentOrchestratorService


class AgentRunService:
    @staticmethod
    def run(
        repository_url,
        installation_id,
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

        try:
            if not repository_url:
                raise ValueError("repository_url is required")

            if not installation_id:
                raise ValueError("installation_id is required")

            if not project_id:
                raise ValueError("project_id is required")

            if not user_id:
                raise ValueError("user_id is required")

            if not user_request:
                raise ValueError("user_request is required")

            repository = RepositoryService.prepare_repository(
                repository_url=repository_url,
                installation_id=installation_id,
            )

            agent_run.base_branch = repository.get("default_branch")
            agent_run.base_commit_sha = repository.get("commit_sha")
            db.commit()

            index_result = CodeIndexerService.index_repository(
                db=db,
                repository_path=repository["local_path"],
                project_id=project_id,
                user_id=user_id,
                repository_url=repository_url,
                commit_sha=repository["commit_sha"],
            )

            result = AgentOrchestratorService.run(
                db=db,
                repository_path=repository["local_path"],
                project_id=project_id,
                user_id=user_id,
                repository_url=repository_url,
                commit_sha=repository["commit_sha"],
                user_request=user_request,
                installation_id=installation_id,
            )

            commit_result = result.get("commit", {})
            pull_request = result.get("pull_request", {})
            validation = result.get("validation", {})
            test_result = result.get("test_result", {})
            plan = result.get("plan", {})

            agent_run.status = "completed"
            agent_run.agent_branch = result.get("branch")
            agent_run.agent_commit_sha = AgentRunService._get_commit_sha(
    commit_result
)
            agent_run.pr_number = pull_request.get("number")
            agent_run.pr_url = pull_request.get("url")
            agent_run.goal = plan.get("goal")
            agent_run.validation_status = (
                "passed"
                if validation.get("safe") is True
                else "failed"
            )
            agent_run.test_status = (
                "passed"
                if test_result.get("passed") is True
                else "failed"
            )
            agent_run.repair_iterations = result.get(
                "repair_iterations",
                0,
            )
            agent_run.completed_at = datetime.utcnow()

            db.commit()
            db.refresh(agent_run)

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

            raise

        finally:
            db.close()

            if repository:
                RepositoryService.cleanup_repository(
                    repository["local_path"]
                )

    @staticmethod
    def _get_commit_sha(
        commit_result: dict,
    ) -> str | None:

        stdout = commit_result.get("stdout", "")

        if not stdout:
            return None

        first_line = stdout.splitlines()[0].strip()

        if not first_line:
            return None

        match = first_line.split()

        if len(match) < 2:
            return None

        commit_sha = match[1]

        if len(commit_sha) < 7:
            return None

        return commit_sha