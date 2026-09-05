from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.db.models import Project, User
from app.services.github_service import GitHubService
from app.services.repository_service import RepositoryService
from app.services.github_app_service import GitHubAppService


router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    repository_url: str


@router.post("/projects")
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.github_access_token:
        raise HTTPException(
            status_code=403,
            detail="GitHub account is not connected",
        )

    if not RepositoryService.validate_github_url(
        project_data.repository_url
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid GitHub repository URL",
        )

    repository_parts = (
        project_data.repository_url
        .rstrip("/")
        .split("/")
    )

    owner = repository_parts[-2]
    repository = repository_parts[-1]

    try:
        access_token = GitHubAppService.get_installation_token_for_user(
    current_user
)

        github_repository = GitHubService.get_repository(
            owner=owner,
            repository=repository,
            access_token=access_token,
        )

    except Exception:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this GitHub repository",
        )

    if (
        github_repository["owner"].lower()
        != current_user.github_username.lower()
    ):
        raise HTTPException(
            status_code=403,
            detail="GitHub repository is not owned by the connected account",
        )

    project = Project(
        name=project_data.name,
        repository_url=github_repository["html_url"],
        owner_id=current_user.id,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


@router.get("/projects")
def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    projects = (
        db.query(Project)
        .filter(Project.owner_id == current_user.id)
        .all()
    )

    return projects


@router.get("/projects/{project_id}")
def get_project(
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

    return project


@router.delete("/projects/{project_id}")
def delete_project(
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

    db.delete(project)
    db.commit()

    return {
        "message": "Project deleted successfully"
    }