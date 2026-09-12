from app.db.database import SessionLocal
from app.services.agent_orchestrator_service import AgentOrchestratorService


db = SessionLocal()

try:
    result = AgentOrchestratorService.run(
        db=db,
        repository_path="rag_test_repo",
        project_id=4,
        user_id=3,
        repository_url="local://rag_test_repo",
        commit_sha="rag-test-001",
        user_request="Update the total price calculation to include shipping cost.",
    )

    print(result)

finally:
    db.close()