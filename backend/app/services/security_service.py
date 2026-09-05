import os
import re


class SecurityService:

    PROTECTED_FILES = {
        ".env",
        ".env.local",
        ".env.production",
        ".env.development",
        "id_rsa",
        "id_ed25519",
    }

    SECRET_PATTERNS = [
        re.compile(
            r"(?i)(api[_-]?key|secret|password|token)"
            r"\s*[:=]\s*['\"][^'\"]+['\"]"
        ),
        re.compile(
            r"(?i)github_pat_[A-Za-z0-9_]+"
        ),
        re.compile(
            r"(?i)ghp_[A-Za-z0-9]+"
        ),
    ]

    @classmethod
    def validate_changed_files(
        cls,
        repository_path: str,
        allowed_files: list,
    ) -> dict:

        allowed = {
            os.path.normpath(path).replace("\\", "/")
            for path in allowed_files
        }

        status = cls._get_git_status(
            repository_path
        )

        if status is None:
            return {
                "passed": False,
                "reason": "Unable to inspect Git status",
                "unexpected_files": [],
                "protected_files": [],
                "secret_files": [],
            }

        changed_files = []

        for line in status.splitlines():

            if not line.strip():
                continue

            file_path = line[3:].strip()

            if " -> " in file_path:
                file_path = file_path.split(
                    " -> ",
                    1,
                )[1]

            file_path = (
                os.path.normpath(file_path)
                .replace("\\", "/")
            )

            changed_files.append(file_path)

        unexpected_files = [
            path
            for path in changed_files
            if path not in allowed
        ]

        protected_files = [
            path
            for path in changed_files
            if os.path.basename(path).lower()
            in cls.PROTECTED_FILES
        ]

        secret_files = []

        for path in changed_files:

            full_path = os.path.join(
                repository_path,
                path.replace("/", os.sep),
            )

            if not os.path.isfile(full_path):
                continue

            try:
                with open(
                    full_path,
                    "r",
                    encoding="utf-8",
                    errors="ignore",
                ) as file:
                    content = file.read()

            except OSError:
                continue

            for pattern in cls.SECRET_PATTERNS:

                if pattern.search(content):
                    secret_files.append(path)
                    break

        passed = not (
            unexpected_files
            or protected_files
            or secret_files
        )

        return {
            "passed": passed,
            "reason": (
                "Git changes passed security validation"
                if passed
                else "Git changes failed security validation"
            ),
            "changed_files": changed_files,
            "unexpected_files": unexpected_files,
            "protected_files": protected_files,
            "secret_files": secret_files,
        }

    @staticmethod
    def _get_git_status(
        repository_path: str,
    ) -> str | None:

        import subprocess

        result = subprocess.run(
            [
                "git",
                "status",
                "--short",
            ],
            cwd=repository_path,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return None

        return result.stdout