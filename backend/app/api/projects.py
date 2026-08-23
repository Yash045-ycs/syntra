from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import Project


router = APIRouter()


# -------------------------
# Database dependency
# -------------------------

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# -------------------------
# Request schema
# -------------------------

class ProjectCreate(BaseModel):
    name: str
    repository_url: str


# -------------------------
# Create project
# -------------------------

@router.post("/projects")
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
):
    project = Project(
        name=project_data.name,
        repository_url=project_data.repository_url,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


# -------------------------
# Get all projects
# -------------------------

@router.get("/projects")
def get_projects(
    db: Session = Depends(get_db),
):
    projects = db.query(Project).all()

    return projects


# -------------------------
# Get project by ID
# -------------------------

@router.get("/projects/{project_id}")
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return project


# -------------------------
# Delete project
# -------------------------

@router.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id)
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