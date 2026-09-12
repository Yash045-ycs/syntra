from app.db.database import SessionLocal
from app.services.code_indexer_service import CodeIndexerService

db = SessionLocal()

try:
    result = CodeIndexerService.index_repository(
        db=db,
        repository_path="rag_test_repo",
        project_id=4,
        user_id=3,
        repository_url="https://github.com/Yash045-ycs/portfolio",
        commit_sha="rag-test-001",
    )

    print(result)

finally:
    db.close()
