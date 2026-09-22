import re

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

        semantic_results = [
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

        explicit_files = cls._extract_file_references(
            query
        )

        if not explicit_files:
            return semantic_results

        filename_results = cls._get_explicit_file_results(
            db=db,
            project_id=project_id,
            user_id=user_id,
            commit_sha=commit_sha,
            file_names=explicit_files,
        )

        return cls._merge_results(
            semantic_results=semantic_results,
            filename_results=filename_results,
            top_k=top_k,
        )

    @staticmethod
    def _extract_file_references(
        query: str,
    ) -> list[str]:

        normalized_query = query.strip()

        candidates = []

        extension_pattern = re.compile(
            r"(?<![\w./-])"
            r"([A-Za-z0-9_.-]+/"
            r"[A-Za-z0-9_./-]+"
            r"|[A-Za-z0-9_.-]+\.[A-Za-z0-9]+)"
            r"(?![\w./-])"
        )

        for match in extension_pattern.findall(
            normalized_query
        ):
            candidates.append(
                match.strip("`'\".,;:()[]{}")
            )

        known_files = [
            "README",
            "README.md",
            "Dockerfile",
            "docker-compose.yml",
            "docker-compose.yaml",
            "package.json",
            "package-lock.json",
            "requirements.txt",
            "pyproject.toml",
            "tsconfig.json",
            "vite.config.ts",
            "vite.config.js",
            "alembic.ini",
            ".env",
            ".gitignore",
        ]

        lowered_query = normalized_query.lower()

        for known_file in known_files:
            if known_file.lower() in lowered_query:
                candidates.append(known_file)

        unique = []

        for candidate in candidates:
            if not candidate:
                continue

            if candidate not in unique:
                unique.append(candidate)

        return unique

    @staticmethod
    def _get_explicit_file_results(
        db: Session,
        project_id: int,
        user_id: int,
        commit_sha: str,
        file_names: list[str],
    ) -> list[dict]:

        if not file_names:
            return []

        conditions = []

        for file_name in file_names:
            normalized = file_name.strip()

            if not normalized:
                continue

            conditions.append(
                CodeEmbedding.file_path == normalized
            )

            conditions.append(
                CodeEmbedding.file_path.ilike(
                    f"%/{normalized}"
                )
            )

        if not conditions:
            return []

        from sqlalchemy import or_

        statement = (
            select(CodeEmbedding)
            .where(
                CodeEmbedding.project_id == project_id,
                CodeEmbedding.user_id == user_id,
                CodeEmbedding.commit_sha == commit_sha,
                or_(*conditions),
            )
            .order_by(
                CodeEmbedding.file_path,
                CodeEmbedding.chunk_index,
            )
        )

        results = db.execute(statement).scalars().all()

        return [
            {
                "file_path": embedding.file_path,
                "language": embedding.language,
                "chunk_index": embedding.chunk_index,
                "content": embedding.content,
                "similarity": 1.0,
                "project_id": embedding.project_id,
                "user_id": embedding.user_id,
                "commit_sha": embedding.commit_sha,
            }
            for embedding in results
        ]

    @staticmethod
    def _merge_results(
        semantic_results: list[dict],
        filename_results: list[dict],
        top_k: int,
    ) -> list[dict]:

        merged = []
        seen = set()

        for result in filename_results:
            key = (
                result["file_path"],
                result["chunk_index"],
            )

            if key in seen:
                continue

            seen.add(key)
            merged.append(result)

        for result in semantic_results:
            key = (
                result["file_path"],
                result["chunk_index"],
            )

            if key in seen:
                continue

            seen.add(key)
            merged.append(result)

        return merged[:top_k]
