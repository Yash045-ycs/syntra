import hashlib
import os
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.models import CodeEmbedding
from app.services.code_chunker_service import CodeChunkerService
from app.services.embedding_service import EmbeddingService


class CodeIndexerService:

    IGNORED_DIRECTORIES = {
        ".git",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "dist",
        "build",
        ".next",
        ".nuxt",
        ".dart_tool",
        ".idea",
        ".vscode",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "coverage",
        ".gradle",
        "target",
        "bin",
        "obj",
    }

    IGNORED_FILES = {
        ".env",
        ".env.local",
        ".env.production",
        ".env.development",
        "id_rsa",
        "id_ed25519",
    }

    MAX_FILE_SIZE = 1024 * 1024

    @classmethod
    def index_repository(
        cls,
        db: Session,
        repository_path: str,
        project_id: int,
        user_id: int,
        repository_url: str,
        commit_sha: str,
    ) -> dict:

        files = cls._collect_files(
            repository_path
        )

        all_chunks = []

        for file_path in files:

            relative_path = os.path.relpath(
                file_path,
                repository_path,
            ).replace("\\", "/")

            try:
                content = Path(file_path).read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
            except OSError:
                continue

            chunks = CodeChunkerService.chunk_file(
                relative_path,
                content,
            )

            language = cls._detect_language(
                relative_path
            )

            for chunk in chunks:
                chunk["language"] = language

            all_chunks.extend(chunks)

        if not all_chunks:
            return {
                "indexed": 0,
                "files": 0,
                "chunks": 0,
                "commit_sha": commit_sha,
            }

        texts = [
            chunk["content"]
            for chunk in all_chunks
        ]

        embeddings = (
            EmbeddingService.generate_embeddings(
                texts
            )
        )

        db.execute(
            delete(CodeEmbedding).where(
                CodeEmbedding.project_id == project_id,
                CodeEmbedding.user_id == user_id,
                CodeEmbedding.commit_sha == commit_sha,
            )
        )

        records = []

        for chunk, embedding in zip(
            all_chunks,
            embeddings,
        ):
            records.append(
                CodeEmbedding(
                    project_id=project_id,
                    user_id=user_id,
                    repository_url=repository_url,
                    commit_sha=commit_sha,
                    file_path=chunk["file_path"],
                    language=chunk["language"],
                    chunk_index=chunk["chunk_index"],
                    content=chunk["content"],
                    embedding=embedding,
                )
            )

        db.add_all(records)
        db.commit()

        indexed_files = len(
            {
                chunk["file_path"]
                for chunk in all_chunks
            }
        )

        return {
            "indexed": True,
            "files": indexed_files,
            "chunks": len(records),
            "commit_sha": commit_sha,
        }

    @classmethod
    def _collect_files(
        cls,
        repository_path: str,
    ) -> list[str]:

        files = []

        for root, directories, filenames in os.walk(
            repository_path
        ):

            directories[:] = [
                directory
                for directory in directories
                if directory not in cls.IGNORED_DIRECTORIES
            ]

            for filename in filenames:

                if filename in cls.IGNORED_FILES:
                    continue

                file_path = os.path.join(
                    root,
                    filename,
                )

                try:
                    if os.path.getsize(
                        file_path
                    ) > cls.MAX_FILE_SIZE:
                        continue
                except OSError:
                    continue

                if not CodeChunkerService.SUPPORTED_EXTENSIONS.__contains__(
                    Path(filename).suffix.lower()
                ):
                    continue

                files.append(file_path)

        return sorted(files)

    @staticmethod
    def _detect_language(
        file_path: str,
    ) -> str:

        extension = Path(
            file_path
        ).suffix.lower()

        languages = {
            ".py": "Python",
            ".js": "JavaScript",
            ".jsx": "JavaScript",
            ".ts": "TypeScript",
            ".tsx": "TypeScript",
            ".java": "Java",
            ".cpp": "C++",
            ".cc": "C++",
            ".cxx": "C++",
            ".c": "C",
            ".h": "C/C++",
            ".hpp": "C++",
            ".dart": "Dart",
            ".go": "Go",
            ".rs": "Rust",
            ".kt": "Kotlin",
            ".kts": "Kotlin",
            ".swift": "Swift",
            ".php": "PHP",
            ".rb": "Ruby",
            ".cs": "C#",
            ".html": "HTML",
            ".css": "CSS",
            ".scss": "SCSS",
            ".sql": "SQL",
            ".sh": "Shell",
            ".md": "Markdown",
            ".json": "JSON",
            ".yaml": "YAML",
            ".yml": "YAML",
            ".xml": "XML",
        }

        return languages.get(
            extension,
            "Unknown",
        )

    @staticmethod
    def _generate_commit_fallback(
        repository_path: str,
    ) -> str:

        digest = hashlib.sha256()

        for root, _, filenames in os.walk(
            repository_path
        ):
            for filename in sorted(filenames):

                path = os.path.join(
                    root,
                    filename,
                )

                if not os.path.isfile(path):
                    continue

                try:
                    with open(
                        path,
                        "rb",
                    ) as file:
                        digest.update(
                            file.read()
                        )
                except OSError:
                    continue

        return digest.hexdigest()