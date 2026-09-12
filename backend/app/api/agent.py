from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.db.models import AgentRun, Project, User
from app.services.agent_run_service import AgentRunService
from app.services.github_service import GitHubService

router = APIRouter()


class AgentRequest(BaseModel):
    request: str


@router.post("/projects/{project_id}/agent/run")
def run_project_agent(
    project_id: int,
    agent_request: AgentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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

    if not current_user.github_access_token:
        raise HTTPException(
            status_code=403,
            detail="GitHub account is not connected",
        )

    if not agent_request.request.strip():
        raise HTTPException(
            status_code=400,
            detail="Change request cannot be empty",
        )

    try:
        installation_id = current_user.github_installation_id

        if not installation_id:
            raise HTTPException(
                status_code=403,
                detail="GitHub App is not installed",
            )

        result = AgentRunService.run(
            repository_url=project.repository_url,
            installation_id=installation_id,
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

    if not current_user.github_installation_id:
        raise HTTPException(
            status_code=403,
            detail="GitHub App is not installed",
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

    try:
        access_token = GitHubService.create_installation_token(
            current_user.github_installation_id
        )

        files = GitHubService.get_pull_request_files(
            owner=owner,
            repository=repository,
            pull_number=agent_run.pr_number,
            access_token=access_token,
        )

        return {
            "run_id": agent_run.id,
            "pr_number": agent_run.pr_number,
            "files": files,
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

@router.get("/projects/{project_id}/runs/{run_id}/pr")
def get_agent_run_pr_status(
    project_id: int,
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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

    if not current_user.github_installation_id:
        raise HTTPException(
            status_code=403,
            detail="GitHub App is not installed",
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

    try:
        access_token = GitHubService.create_installation_token(
            current_user.github_installation_id
        )

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