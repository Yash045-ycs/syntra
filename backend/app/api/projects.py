from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.db.models import Project, User
from app.services.github_service import GitHubService
from app.services.repository_service import RepositoryService
from app.services.token_encryption_service import TokenEncryptionService


router = APIRouter()


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    repository_url: str = Field(min_length=1, max_length=500)


@router.post(
    "/projects",
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.github_access_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="GitHub account is not connected",
        )

    if not current_user.github_username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="GitHub username is not available",
        )

    repository_url = project_data.repository_url.strip()

    if not RepositoryService.validate_github_url(repository_url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub repository URL",
        )

    repository_parts = repository_url.rstrip("/").split("/")

    if len(repository_parts) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub repository URL",
        )

    owner = repository_parts[-2]
    repository = repository_parts[-1]

    if repository.endswith(".git"):
        repository = repository[:-4]

    if not owner or not repository:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub repository URL",
        )

    existing_project = db.scalar(
        select(Project).where(
            Project.owner_id == current_user.id,
            Project.repository_url.ilike(
                f"https://github.com/{owner}/{repository}"
            ),
        )
    )

    if existing_project:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This repository is already added to your Syntra projects",
        )

    try:
        access_token = TokenEncryptionService.decrypt(
            current_user.github_access_token
        )

        github_repository = GitHubService.get_repository(
            owner=owner,
            repository=repository,
            access_token=access_token,
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this GitHub repository",
        )

    github_owner = github_repository.get("owner")

    if not github_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unable to verify GitHub repository ownership",
        )

    if (
        github_owner.lower()
        != current_user.github_username.lower()
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="GitHub repository is not owned by the connected account",
        )

    project = Project(
        name=project_data.name.strip(),
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
            status_code=status.HTTP_404_NOT_FOUND,
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    db.delete(project)
    db.commit()

    return {
        "message": "Project deleted successfully"
    }