from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import SessionLocal
from app.db.models import Project, User
from app.services.repository_service import RepositoryService
from app.services.scanner_service import ScannerService


router = APIRouter()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post("/projects/{project_id}/analyze")
def analyze_project(
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

    repository_path = None

    try:
        repository_path = RepositoryService.clone_repository(
            project.repository_url
        )

        analysis = ScannerService.scan_repository(
            repository_path
        )

        return {
            "project_id": project.id,
            "project_name": project.name,
            "repository_url": project.repository_url,
            "analysis": analysis,
        }

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

    finally:
        RepositoryService.cleanup_repository(
            repository_path
        )