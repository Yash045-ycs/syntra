from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.db.models import ActivityLog, User

router = APIRouter(
    prefix="/activity",
    tags=["Activity"],
)


@router.get("")
def get_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logs = (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == current_user.id)
        .order_by(ActivityLog.created_at.desc())
        .limit(100)
        .all()
    )

    return [
        {
            "id": log.id,
            "project_id": log.project_id,
            "agent_run_id": log.agent_run_id,
            "event_type": log.event_type,
            "message": log.message,
            "created_at": log.created_at,
        }
        for log in logs
    ]


@router.get("/projects/{project_id}")
def get_project_activity(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logs = (
        db.query(ActivityLog)
        .filter(
            ActivityLog.project_id == project_id,
            ActivityLog.user_id == current_user.id,
        )
        .order_by(ActivityLog.created_at.desc())
        .limit(100)
        .all()
    )

    return [
        {
            "id": log.id,
            "project_id": log.project_id,
            "agent_run_id": log.agent_run_id,
            "event_type": log.event_type,
            "message": log.message,
            "created_at": log.created_at,
        }
        for log in logs
    ]