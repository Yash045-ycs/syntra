from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    github_user_id: Mapped[int | None] = mapped_column(
        Integer,
        unique=True,
        nullable=True,
        index=True,
    )

    github_username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    github_access_token: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    github_installation_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    projects: Mapped[list["Project"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )

    agent_runs: Mapped[list["AgentRun"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class GitHubOAuthState(Base):
    __tablename__ = "github_oauth_states"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    state: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    user: Mapped["User"] = relationship()


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    repository_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    owner: Mapped["User"] = relationship(
        back_populates="projects",
    )

    agent_runs: Mapped[list["AgentRun"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )


class CodeEmbedding(Base):
    __tablename__ = "code_embeddings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    repository_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    commit_sha: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    file_path: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    language: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    embedding: Mapped[list[float]] = mapped_column(
        Vector(768),
        nullable=False,
    )

    project: Mapped["Project"] = relationship()

    user: Mapped["User"] = relationship()


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    user_request: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    base_branch: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    agent_branch: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    base_commit_sha: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    agent_commit_sha: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    pr_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    pr_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    goal: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    validation_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    test_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    repair_iterations: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    project: Mapped["Project"] = relationship(
        back_populates="agent_runs",
    )

    user: Mapped["User"] = relationship(
        back_populates="agent_runs",
    )