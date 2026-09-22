import os
import shutil
import tempfile
from pathlib import Path


class CodeChangeApplierService:

    PROTECTED_FILES = {
        ".env",
        ".env.local",
        ".env.production",
        ".env.development",
        "id_rsa",
        "id_ed25519",
    }

    PROTECTED_DIRECTORIES = {
        ".git",
        ".venv",
        "venv",
        "node_modules",
    }

    @classmethod
    def apply_changes(
        cls,
        repository_path: str,
        changes: list[dict],
    ) -> dict:

        repository = Path(repository_path).resolve()

        if not repository.exists():
            raise ValueError(
                f"Repository does not exist: {repository}"
            )

        if not repository.is_dir():
            raise ValueError(
                f"Repository path is not a directory: {repository}"
            )

        backup_directory = Path(
            tempfile.mkdtemp(
                prefix="syntra_backup_"
            )
        )

        applied = []
        backups = []
        created_files = []

        try:
            for change in changes:

                if not isinstance(change, dict):
                    raise ValueError(
                        "Each change must be an object"
                    )

                file_path = change.get("file_path")
                action = change.get("action")
                content = change.get("content")

                if not file_path:
                    raise ValueError(
                        "Change is missing file_path"
                    )

                if action not in {"modify", "create"}:
                    raise ValueError(
                        f"Unsupported action: {action}"
                    )

                if not isinstance(content, str):
                    raise ValueError(
                        f"Content must be a string for {file_path}"
                    )

                target = cls._validate_path(
                    repository,
                    file_path,
                )

                if action == "modify":
                    cls._apply_modify(
                        target=target,
                        file_path=file_path,
                        content=content,
                        backup_directory=backup_directory,
                        backups=backups,
                    )

                elif action == "create":
                    cls._apply_create(
                        target=target,
                        file_path=file_path,
                        content=content,
                        created_files=created_files,
                    )

                applied.append({
                    "file_path": file_path,
                    "action": action,
                })

            return {
                "applied": applied,
                "backups": backups,
                "created_files": created_files,
                "backup_directory": str(backup_directory),
                "count": len(applied),
            }

        except Exception:
            cls.restore_changes(
                repository_path=repository_path,
                backups=backups,
                created_files=created_files,
            )

            shutil.rmtree(
                backup_directory,
                ignore_errors=True,
            )

            raise

    @classmethod
    def _apply_modify(
        cls,
        target: Path,
        file_path: str,
        content: str,
        backup_directory: Path,
        backups: list[dict],
    ) -> None:

        if not target.exists():
            raise ValueError(
                f"Target file does not exist: {file_path}"
            )

        if not target.is_file():
            raise ValueError(
                f"Target is not a file: {file_path}"
            )

        original_content = target.read_text(
            encoding="utf-8",
            errors="strict",
        )

        backup_path = backup_directory / Path(
            file_path
        )

        backup_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        backup_path.write_text(
            original_content,
            encoding="utf-8",
        )

        backups.append({
            "file_path": file_path,
            "backup_path": str(backup_path),
        })

        target.write_text(
            content,
            encoding="utf-8",
        )

    @classmethod
    def _apply_create(
        cls,
        target: Path,
        file_path: str,
        content: str,
        created_files: list[str],
    ) -> None:

        if target.exists():
            raise ValueError(
                f"Target file already exists: {file_path}"
            )

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        target.write_text(
            content,
            encoding="utf-8",
        )

        created_files.append(file_path)

    @classmethod
    def restore_changes(
        cls,
        repository_path: str,
        backups: list[dict],
        created_files: list[str] | None = None,
    ) -> None:

        repository = Path(repository_path).resolve()

        if created_files:
            for file_path in reversed(created_files):

                target = cls._validate_path(
                    repository,
                    file_path,
                )

                if target.exists() and target.is_file():
                    target.unlink()

                cls._remove_empty_parent_directories(
                    repository,
                    target.parent,
                )

        for backup in reversed(backups):

            file_path = backup["file_path"]
            backup_path = Path(
                backup["backup_path"]
            )

            target = cls._validate_path(
                repository,
                file_path,
            )

            if not backup_path.exists():
                continue

            target.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            shutil.copy2(
                backup_path,
                target,
            )

    @classmethod
    def _remove_empty_parent_directories(
        cls,
        repository: Path,
        directory: Path,
    ) -> None:

        current = directory

        while current != repository:

            try:
                current.relative_to(repository)
            except ValueError:
                break

            try:
                current.rmdir()
            except OSError:
                break

            current = current.parent

    @classmethod
    def cleanup_backups(
        cls,
        backup_directory: str,
    ) -> None:

        shutil.rmtree(
            backup_directory,
            ignore_errors=True,
        )

    @classmethod
    def _validate_path(
        cls,
        repository: Path,
        file_path: str,
    ) -> Path:

        normalized = file_path.replace("\\", "/").strip()

        if not normalized:
            raise ValueError(
                "File path cannot be empty"
            )

        if os.path.isabs(normalized):
            raise ValueError(
                f"Absolute paths are not allowed: {file_path}"
            )

        parts = Path(normalized).parts

        if ".." in parts:
            raise ValueError(
                f"Path traversal detected: {file_path}"
            )

        if parts[0] in cls.PROTECTED_DIRECTORIES:
            raise ValueError(
                f"Protected directory cannot be modified: {file_path}"
            )

        filename = Path(normalized).name

        if filename in cls.PROTECTED_FILES:
            raise ValueError(
                f"Protected file cannot be modified: {file_path}"
            )

        target = (repository / normalized).resolve()

        try:
            target.relative_to(repository)
        except ValueError as exc:
            raise ValueError(
                f"Path escapes repository: {file_path}"
            ) from exc

        return target
