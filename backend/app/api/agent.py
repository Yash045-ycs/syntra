from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.db.models import AgentRun, Project, User
from app.services.agent_run_service import AgentRunService
from app.services.github_service import GitHubService
from app.services.repository_index_service import RepositoryIndexService
from app.services.token_encryption_service import TokenEncryptionService

router = APIRouter()


class AgentRequest(BaseModel):
    request: str


def get_github_access_token(
    current_user: User,
) -> str:

    if not current_user.github_access_token:
        raise HTTPException(
            status_code=403,
            detail="GitHub account is not connected",
        )

    try:
        access_token = TokenEncryptionService.decrypt(
            current_user.github_access_token
        )
    except Exception:
        raise HTTPException(
            status_code=403,
            detail="GitHub connection is invalid. Please reconnect GitHub.",
        )

    if not access_token:
        raise HTTPException(
            status_code=403,
            detail="GitHub connection is invalid. Please reconnect GitHub.",
        )

    return access_token


def get_owned_project(
    project_id: int,
    db: Session,
    current_user: User,
) -> Project:

    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.owner_id == current_user.id,
        )
        .first()
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return project


@router.post("/projects/{project_id}/analyze")
def analyze_project_repository(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_owned_project(
        project_id=project_id,
        db=db,
        current_user=current_user,
    )

    access_token = get_github_access_token(
        current_user
    )

    try:
        result = (
            RepositoryIndexService.prepare_and_index_repository(
                repository_url=project.repository_url,
                access_token=access_token,
                project_id=project.id,
                user_id=current_user.id,
            )
        )

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.post("/projects/{project_id}/agent/run")
def run_project_agent(
    project_id: int,
    agent_request: AgentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_owned_project(
        project_id=project_id,
        db=db,
        current_user=current_user,
    )

    access_token = get_github_access_token(
        current_user
    )

    if not agent_request.request.strip():
        raise HTTPException(
            status_code=400,
            detail="Change request cannot be empty",
        )

    try:
        result = AgentRunService.run(
            repository_url=project.repository_url,
            access_token=access_token,
            project_id=project.id,
            user_id=current_user.id,
            user_request=agent_request.request.strip(),
        )

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.get("/projects/{project_id}/runs/{run_id}")
def get_agent_run(
    project_id: int,
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_owned_project(
        project_id=project_id,
        db=db,
        current_user=current_user,
    )

    agent_run = (
        db.query(AgentRun)
        .filter(
            AgentRun.id == run_id,
            AgentRun.project_id == project_id,
            AgentRun.user_id == current_user.id,
        )
        .first()
    )

    if agent_run is None:
        raise HTTPException(
            status_code=404,
            detail="Agent run not found",
        )

    return {
        "id": agent_run.id,
        "project_id": agent_run.project_id,
        "user_id": agent_run.user_id,
        "status": agent_run.status,
        "user_request": agent_run.user_request,
        "base_branch": agent_run.base_branch,
        "agent_branch": agent_run.agent_branch,
        "base_commit_sha": agent_run.base_commit_sha,
        "agent_commit_sha": agent_run.agent_commit_sha,
        "pr_number": agent_run.pr_number,
        "pr_url": agent_run.pr_url,
        "goal": agent_run.goal,
        "validation_status": agent_run.validation_status,
        "test_status": agent_run.test_status,
        "repair_iterations": agent_run.repair_iterations,
        "error": agent_run.error,
        "created_at": agent_run.created_at,
        "completed_at": agent_run.completed_at,
    }


@router.get("/projects/{project_id}/runs")
def get_agent_runs(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_owned_project(
        project_id=project_id,
        db=db,
        current_user=current_user,
    )

    agent_runs = (
        db.query(AgentRun)
        .filter(
            AgentRun.project_id == project_id,
            AgentRun.user_id == current_user.id,
        )
        .order_by(AgentRun.created_at.desc())
        .all()
    )

    return [
        {
            "id": run.id,
            "project_id": run.project_id,
            "status": run.status,
            "user_request": run.user_request,
            "base_branch": run.base_branch,
            "agent_branch": run.agent_branch,
            "base_commit_sha": run.base_commit_sha,
            "agent_commit_sha": run.agent_commit_sha,
            "pr_number": run.pr_number,
            "pr_url": run.pr_url,
            "goal": run.goal,
            "validation_status": run.validation_status,
            "test_status": run.test_status,
            "repair_iterations": run.repair_iterations,
            "error": run.error,
            "created_at": run.created_at,
            "completed_at": run.completed_at,
        }
        for run in agent_runs
    ]

@router.get("/projects/{project_id}/runs/{run_id}/diff")
def get_agent_run_diff(
    project_id: int,
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_owned_project(
        project_id=project_id,
        db=db,
        current_user=current_user,
    )

    agent_run = (
        db.query(AgentRun)
        .filter(
            AgentRun.id == run_id,
            AgentRun.project_id == project_id,
            AgentRun.user_id == current_user.id,
        )
        .first()
    )

    if agent_run is None:
        raise HTTPException(
            status_code=404,
            detail="Agent run not found",
        )

    if not agent_run.pr_number:
        raise HTTPException(
            status_code=404,
            detail="No pull request is associated with this run",
        )

    access_token = get_github_access_token(
        current_user
    )

    repository_url = project.repository_url.rstrip("/")
    parts = repository_url.split("/")

    if len(parts) < 2:
        raise HTTPException(
            status_code=400,
            detail="Invalid repository URL",
        )

    owner = parts[-2]
    repository = parts[-1]

    if repository.endswith(".git"):
        repository = repository[:-4]

    try:
        files = GitHubService.get_pull_request_files(
            owner=owner,
            repository=repository,
            pull_number=agent_run.pr_number,
            access_token=access_token,
        )

        total_additions = 0
        total_deletions = 0

        normalized_files = []

        for file in files:
            additions = file.get("additions", 0)
            deletions = file.get("deletions", 0)

            total_additions += additions
            total_deletions += deletions

            normalized_files.append(
                {
                    "filename": file.get("filename"),
                    "status": file.get("status"),
                    "additions": additions,
                    "deletions": deletions,
                    "changes": file.get("changes", 0),
                    "patch": file.get("patch"),
                }
            )

        return {
            "run_id": agent_run.id,
            "pr_number": agent_run.pr_number,
            "files": normalized_files,
            "summary": {
                "files_changed": len(normalized_files),
                "additions": total_additions,
                "deletions": total_deletions,
            },
        }

    except RuntimeError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

@router.post("/projects/{project_id}/runs/{run_id}/approve")
def approve_agent_run(
    project_id: int,
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_owned_project(
        project_id=project_id,
        db=db,
        current_user=current_user,
    )

    agent_run = (
        db.query(AgentRun)
        .filter(
            AgentRun.id == run_id,
            AgentRun.project_id == project_id,
            AgentRun.user_id == current_user.id,
        )
        .first()
    )

    if agent_run is None:
        raise HTTPException(
            status_code=404,
            detail="Agent run not found",
        )

    if agent_run.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Only completed agent runs can be approved",
        )

    if not agent_run.pr_number:
        raise HTTPException(
            status_code=400,
            detail="Cannot approve a run without a pull request",
        )

    agent_run.status = "approved"

    db.commit()
    db.refresh(agent_run)

    return {
        "id": agent_run.id,
        "project_id": agent_run.project_id,
        "status": agent_run.status,
        "pr_number": agent_run.pr_number,
        "pr_url": agent_run.pr_url,
        "message": "Agent run approved successfully",
    }

@router.post("/projects/{project_id}/runs/{run_id}/merge")
def merge_agent_run(
    project_id: int,
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_owned_project(
        project_id=project_id,
        db=db,
        current_user=current_user,
    )

    agent_run = (
        db.query(AgentRun)
        .filter(
            AgentRun.id == run_id,
            AgentRun.project_id == project_id,
            AgentRun.user_id == current_user.id,
        )
        .first()
    )

    if agent_run is None:
        raise HTTPException(
            status_code=404,
            detail="Agent run not found",
        )

    if agent_run.status != "approved":
        raise HTTPException(
            status_code=400,
            detail="Only approved agent runs can be merged",
        )

    if not agent_run.pr_number:
        raise HTTPException(
            status_code=400,
            detail="Cannot merge a run without a pull request",
        )

    access_token = get_github_access_token(
        current_user
    )

    repository_url = project.repository_url.rstrip("/")
    parts = repository_url.split("/")

    if len(parts) < 2:
        raise HTTPException(
            status_code=400,
            detail="Invalid repository URL",
        )

    owner = parts[-2]
    repository = parts[-1]

    if repository.endswith(".git"):
        repository = repository[:-4]

    try:
        pull_request = GitHubService.get_pull_request(
            owner=owner,
            repository=repository,
            pull_number=agent_run.pr_number,
            access_token=access_token,
        )

        if pull_request["merged"]:
            agent_run.status = "merged"

            db.commit()
            db.refresh(agent_run)

            return {
                "run_id": agent_run.id,
                "status": agent_run.status,
                "pull_request": pull_request,
                "message": "Pull request was already merged",
            }

        if pull_request["state"] != "open":
            raise HTTPException(
                status_code=400,
                detail=(
                    "Pull request is not open and cannot be merged"
                ),
            )

        merge_result = GitHubService.merge_pull_request(
            owner=owner,
            repository=repository,
            pull_number=agent_run.pr_number,
            access_token=access_token,
            merge_method="squash",
        )

        if not merge_result["merged"]:
            raise HTTPException(
                status_code=400,
                detail=merge_result.get(
                    "message",
                    "Pull request could not be merged",
                ),
            )

        agent_run.status = "merged"

        db.commit()
        db.refresh(agent_run)

        return {
            "run_id": agent_run.id,
            "status": agent_run.status,
            "pr_number": agent_run.pr_number,
            "pr_url": agent_run.pr_url,
            "merge": merge_result,
            "message": "Pull request merged successfully",
        }

    except HTTPException:
        raise

    except RuntimeError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

@router.get("/projects/{project_id}/runs/{run_id}/pr")
def get_agent_run_pr_status(
    project_id: int,
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_owned_project(
        project_id=project_id,
        db=db,
        current_user=current_user,
    )

    agent_run = (
        db.query(AgentRun)
        .filter(
            AgentRun.id == run_id,
            AgentRun.project_id == project_id,
            AgentRun.user_id == current_user.id,
        )
        .first()
    )

    if agent_run is None:
        raise HTTPException(
            status_code=404,
            detail="Agent run not found",
        )

    if not agent_run.pr_number:
        raise HTTPException(
            status_code=404,
            detail="No pull request is associated with this run",
        )

    access_token = get_github_access_token(
        current_user
    )

    repository_url = project.repository_url.rstrip("/")
    parts = repository_url.split("/")

    if len(parts) < 2:
        raise HTTPException(
            status_code=400,
            detail="Invalid repository URL",
        )

    owner = parts[-2]
    repository = parts[-1]

    if repository.endswith(".git"):
        repository = repository[:-4]

    try:
        pr = GitHubService.get_pull_request(
            owner=owner,
            repository=repository,
            pull_number=agent_run.pr_number,
            access_token=access_token,
        )

        return {
            "run_id": agent_run.id,
            "database_status": agent_run.status,
            "pull_request": pr,
        }

    except RuntimeError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )