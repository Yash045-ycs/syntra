import os
import shutil
import subprocess
import tempfile
from urllib.parse import urlparse


class RepositoryService:

    @staticmethod
    def validate_github_url(repository_url: str) -> bool:
        parsed = urlparse(repository_url)

        return (
            parsed.scheme in {"http", "https"}
            and parsed.netloc.lower() in {
                "github.com",
                "www.github.com",
            }
            and len(parsed.path.strip("/").split("/")) == 2
        )

    @staticmethod
    def clone_repository(repository_url: str) -> str:
        if not RepositoryService.validate_github_url(repository_url):
            raise ValueError("Invalid GitHub repository URL")

        temp_dir = tempfile.mkdtemp(prefix="syntra_repo_")

        try:
            result = subprocess.run(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    repository_url,
                    temp_dir,
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                shutil.rmtree(temp_dir, ignore_errors=True)

                raise RuntimeError(
                    result.stderr.strip()
                    or "Failed to clone repository"
                )

            return temp_dir

        except subprocess.TimeoutExpired:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError("Repository cloning timed out")

        except FileNotFoundError:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError("Git is not installed or not available in PATH")

    @staticmethod
    def cleanup_repository(repository_path: str) -> None:
        if repository_path and os.path.exists(repository_path):
            shutil.rmtree(repository_path, ignore_errors=True)