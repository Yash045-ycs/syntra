from app.db.database import SessionLocal
from app.services.repository_service import RepositoryService
from app.services.code_indexer_service import CodeIndexerService


class RepositoryIndexService:

    @staticmethod
    def prepare_and_index_repository(
        repository_url: str,
        installation_id: int,
        project_id: int,
        user_id: int,
    ) -> dict:

        repository = None
        db = SessionLocal()

        try:
            repository = (
                RepositoryService.prepare_repository(
                    repository_url=repository_url,
                    installation_id=installation_id,
                )
            )

            index_result = (
                CodeIndexerService.index_repository(
                    db=db,
                    repository_path=repository["local_path"],
                    project_id=project_id,
                    user_id=user_id,
                    repository_url=repository_url,
                    commit_sha=repository["commit_sha"],
                )
            )

            return {
                "success": True,
                "repository_url": repository_url,
                "owner": repository["owner"],
                "repository": repository["repository"],
                "full_name": repository["full_name"],
                "default_branch": repository[
                    "default_branch"
                ],
                "private": repository["private"],
                "html_url": repository["html_url"],
                "commit_sha": repository["commit_sha"],
                "index": index_result,
            }

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

            if repository:
                RepositoryService.cleanup_repository(
                    repository["local_path"]
                )
