import re
import subprocess
from pathlib import Path


class DiffSecurityService:

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

    SECRET_PATTERNS = [
        re.compile(
            r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"]+['\"]"
        ),
        re.compile(
            r"(?i)-----BEGIN (RSA|OPENSSH|EC|DSA|PRIVATE) KEY-----"
        ),
        re.compile(
            r"gh[pousr]_[A-Za-z0-9_]{20,}"
        ),
        re.compile(
            r"AIza[0-9A-Za-z_-]{20,}"
        ),
    ]

    MAX_CHANGED_LINES = 1000

    @classmethod
    def validate(
        cls,
        repository_path: str,
        planned_files: list[str],
    ) -> dict:

        repository = Path(repository_path).resolve()

        if not repository.exists():
            raise ValueError(
                f"Repository does not exist: {repository}"
            )

        if not cls._is_git_repository(repository):
            raise ValueError(
                f"Path is not a Git repository: {repository}"
            )

        diff = cls._get_diff(repository)

        changed_files = cls._get_changed_files(repository)

        unexpected_files = [
            file_path
            for file_path in changed_files
            if file_path not in planned_files
        ]

        protected_files = [
            file_path
            for file_path in changed_files
            if cls._is_protected(file_path)
        ]

        secret_matches = cls._find_secrets(diff)

        changed_lines = cls._count_changed_lines(diff)

        errors = []

        if unexpected_files:
            errors.append(
                f"Unexpected files modified: {unexpected_files}"
            )

        if protected_files:
            errors.append(
                f"Protected files modified: {protected_files}"
            )

        if secret_matches:
            errors.append(
                "Potential secrets detected in diff"
            )

        if changed_lines > cls.MAX_CHANGED_LINES:
            errors.append(
                f"Diff is too large: {changed_lines} changed lines"
            )

        return {
            "safe": len(errors) == 0,
            "changed_files": changed_files,
            "planned_files": planned_files,
            "unexpected_files": unexpected_files,
            "protected_files": protected_files,
            "secret_matches": secret_matches,
            "changed_lines": changed_lines,
            "diff": diff,
            "errors": errors,
        }

    @staticmethod
    def _is_git_repository(repository: Path) -> bool:

        result = subprocess.run(
            [
                "git",
                "-C",
                str(repository),
                "rev-parse",
                "--show-toplevel",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode != 0:
            return False

        try:
            git_root = Path(
                result.stdout.strip()
            ).resolve()
        except OSError:
            return False

        return git_root == repository

    @staticmethod
    def _get_diff(repository: Path) -> str:

        result = subprocess.run(
            [
                "git",
                "-C",
                str(repository),
                "diff",
                "--no-ext-diff",
                "--unified=3",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Git diff failed: {result.stderr.strip()}"
            )

        untracked = DiffSecurityService._get_untracked_files(
            repository
        )

        if untracked:
            sections = [result.stdout]

            for file_path in untracked:
                target = repository / file_path

                try:
                    content = target.read_text(
                        encoding="utf-8",
                        errors="replace",
                    )
                except OSError:
                    continue

                sections.append(
                    f"--- /dev/null\n"
                    f"+++ b/{file_path}\n"
                    + "".join(
                        f"+{line}\n"
                        for line in content.splitlines()
                    )
                )

            return "\n".join(sections)

        return result.stdout

    @staticmethod
    def _get_changed_files(repository: Path) -> list[str]:

        tracked_result = subprocess.run(
            [
                "git",
                "-C",
                str(repository),
                "diff",
                "--name-only",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if tracked_result.returncode != 0:
            raise RuntimeError(
                f"Git diff failed: {tracked_result.stderr.strip()}"
            )

        tracked_files = {
            line.strip().replace("\\", "/")
            for line in tracked_result.stdout.splitlines()
            if line.strip()
        }

        untracked_files = set(
            DiffSecurityService._get_untracked_files(
                repository
            )
        )

        return sorted(
            tracked_files | untracked_files
        )

    @staticmethod
    def _get_untracked_files(repository: Path) -> list[str]:

        result = subprocess.run(
            [
                "git",
                "-C",
                str(repository),
                "ls-files",
                "--others",
                "--exclude-standard",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Git status failed: {result.stderr.strip()}"
            )

        return [
            line.strip().replace("\\", "/")
            for line in result.stdout.splitlines()
            if line.strip()
        ]

    @classmethod
    def _find_secrets(
        cls,
        diff: str,
    ) -> list[str]:

        matches = []

        added_lines = [
            line[1:]
            for line in diff.splitlines()
            if line.startswith("+")
            and not line.startswith("+++")
        ]

        for line in added_lines:
            for pattern in cls.SECRET_PATTERNS:
                if pattern.search(line):
                    matches.append(
                        line.strip()
                    )
                    break

        return matches

    @staticmethod
    def _count_changed_lines(
        diff: str,
    ) -> int:

        return sum(
            1
            for line in diff.splitlines()
            if (
                (
                    line.startswith("+")
                    and not line.startswith("+++")
                )
                or (
                    line.startswith("-")
                    and not line.startswith("---")
                )
            )
        )

    @classmethod
    def _is_protected(
        cls,
        file_path: str,
    ) -> bool:

        normalized = file_path.replace("\\", "/")
        parts = Path(normalized).parts

        if any(
            directory in cls.PROTECTED_DIRECTORIES
            for directory in parts
        ):
            return True

        return Path(normalized).name in cls.PROTECTED_FILES
