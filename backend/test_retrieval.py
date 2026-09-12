from app.db.database import SessionLocal
from app.services.code_retrieval_service import CodeRetrievalService

db = SessionLocal()

try:
    results = CodeRetrievalService.search(
        db=db,
        query="How is the total price calculated?",
        project_id=4,
        user_id=3,
        commit_sha="rag-test-001",
        top_k=5,
    )

    for result in results:
        print(
            result["file_path"],
            result["similarity"],
            result["content"],
        )

finally:
    db.close()
