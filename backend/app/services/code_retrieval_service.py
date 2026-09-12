from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CodeEmbedding
from app.services.embedding_service import EmbeddingService


class CodeRetrievalService:

    DEFAULT_TOP_K = 8

    @classmethod
    def search(
        cls,
        db: Session,
        query: str,
        project_id: int,
        user_id: int,
        commit_sha: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> list[dict]:

        if not query.strip():
            return []

        if top_k <= 0:
            return []

        query_embedding = (
            EmbeddingService.generate_embedding(query)
        )

        similarity = (
            1 - CodeEmbedding.embedding.cosine_distance(
                query_embedding
            )
        )

        statement = (
            select(
                CodeEmbedding,
                similarity.label("similarity"),
            )
            .where(
                CodeEmbedding.project_id == project_id,
                CodeEmbedding.user_id == user_id,
                CodeEmbedding.commit_sha == commit_sha,
            )
            .order_by(
                CodeEmbedding.embedding.cosine_distance(
                    query_embedding
                )
            )
            .limit(top_k)
        )

        results = db.execute(statement).all()

        return [
            {
                "file_path": embedding.file_path,
                "language": embedding.language,
                "chunk_index": embedding.chunk_index,
                "content": embedding.content,
                "similarity": float(similarity_score),
                "project_id": embedding.project_id,
                "user_id": embedding.user_id,
                "commit_sha": embedding.commit_sha,
            }
            for embedding, similarity_score in results
        ]