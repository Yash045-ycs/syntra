from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.projects import router as projects_router
from app.api.analysis import router as analysis_router
from app.db.database import Base, engine
from app.db import models


# Create database tables
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Syntra API",
    description="Backend for Syntra - Autonomous AI Engineering Agent",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    health_router,
    prefix="/api",
)

app.include_router(
    projects_router,
    prefix="/api",
)

app.include_router(
    analysis_router,
    prefix="/api",
)

app.include_router(
    auth_router,
    prefix="/api",
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Syntra",
        "status": "running",
    }