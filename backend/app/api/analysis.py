from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import SessionLocal
from app.db.models import Project, User
from app.services.repository_service import RepositoryService
from app.services.scanner_service import ScannerService
from app.services.context_service import CodebaseContextService
from app.services.ai_service import AIService
from app.services.planner_service import PlannerService
from app.services.github_app_service import GitHubAppService


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

    if not current_user.github_access_token:
        raise HTTPException(
            status_code=403,
            detail="GitHub account is not connected",
        )

    repository_path = None

    try:
        access_token = GitHubAppService.get_installation_token_for_user(
            current_user
        )

        print("[Analysis] Starting repository scan")

        repository_path = RepositoryService.clone_repository(
            project.repository_url,
            access_token=access_token,
        )

        print("[Analysis] Clone finished")
        print("[Analysis] Starting scanner")

        analysis = ScannerService.scan_repository(
            repository_path
        )

        print("[Analysis] Scanner finished")

        context = CodebaseContextService.build_context(
            repository_path,
            analysis,
        )

        print("[Analysis] Context building finished")
        print("[Analysis] Starting Gemini analysis")

        ai_analysis = AIService.analyze_codebase(
            context
        )

        print("[Analysis] Gemini analysis finished")

        return {
            "project_id": project.id,
            "project_name": project.name,
            "repository_url": project.repository_url,
            "analysis": analysis,
            "ai_analysis": ai_analysis,
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


class ChangeRequest(BaseModel):
    request: str


@router.post("/projects/{project_id}/plan")
def create_project_plan(
    project_id: int,
    change_request: ChangeRequest,
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

    repository_path = None

    try:
        access_token = GitHubAppService.get_installation_token_for_user(
    current_user
)

        print("[Planning] Starting repository clone")

        repository_path = RepositoryService.clone_repository(
            project.repository_url,
            access_token=access_token,
        )

        print("[Planning] Clone finished")
        print("[Planning] Starting scanner")

        analysis = ScannerService.scan_repository(
            repository_path
        )

        print("[Planning] Scanner finished")

        context = CodebaseContextService.build_context(
            repository_path,
            analysis,
        )

        print("[Planning] Context built")
        print("[Planning] Sending change request to Gemini")

        plan = PlannerService.create_plan(
            change_request.request,
            context,
        )

        print("[Planning] Plan generated")

        return {
            "project_id": project.id,
            "project_name": project.name,
            "change_request": change_request.request,
            "plan": plan,
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