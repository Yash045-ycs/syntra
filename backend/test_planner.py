from app.db.database import SessionLocal
from app.services.code_retrieval_service import CodeRetrievalService
from app.services.code_planner_service import CodePlannerService

db = SessionLocal()

try:
    query = "How is the total price calculated?"

    results = CodeRetrievalService.search(
        db=db,
        query=query,
        project_id=4,
        user_id=3,
        commit_sha="rag-test-001",
        top_k=5,
    )

    plan = CodePlannerService.create_plan(
        user_request=query,
        retrieved_chunks=results,
    )

    print(plan)

finally:
    db.close()
