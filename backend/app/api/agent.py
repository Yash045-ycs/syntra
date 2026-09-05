from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import SessionLocal
from app.db.models import Project, User
from app.services.agent_service import AgentService


router = APIRouter()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


class AgentRequest(BaseModel):
    request: str


@router.post("/projects/{project_id}/execute")
def execute_project_agent(
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
        result = AgentService.execute(
            repository_url=project.repository_url,
            change_request=agent_request.request,
            current_user=current_user,
        )

        return {
            "project_id": project.id,
            "project_name": project.name,
            "result": result,
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