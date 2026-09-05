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
    def clone_repository(
        repository_url: str,
        access_token: str | None = None,
    ) -> str:

        if not RepositoryService.validate_github_url(
            repository_url
        ):
            raise ValueError(
                "Invalid GitHub repository URL"
            )

        temp_parent = tempfile.mkdtemp(
            prefix="syntra_repo_"
        )

        temp_dir = os.path.join(
            temp_parent,
            "repository",
        )

        askpass_path = None

        print(
            f"[Repository] Starting clone: "
            f"{repository_url}"
        )

        print(
            f"[Repository] Temporary directory: "
            f"{temp_dir}"
        )

        try:
            command = [
                "git",
                "-c",
                "credential.helper=",
                "clone",
                "--depth",
                "1",
                "--single-branch",
                repository_url,
                temp_dir,
            ]

            environment = {
                **os.environ,
                "GIT_TERMINAL_PROMPT": "0",
            }

            if access_token:
                askpass_path = os.path.join(
                    temp_parent,
                    ".syntra_git_askpass.cmd",
                )

                with open(
                    askpass_path,
                    "w",
                    encoding="utf-8",
                ) as file:
                    file.write(
                        "@echo off\r\n"
                        "echo %1 | findstr /I \"Username\" >nul\r\n"
                        "if not errorlevel 1 (\r\n"
                        "echo x-access-token\r\n"
                        "exit /b 0\r\n"
                        ")\r\n"
                        "echo %1 | findstr /I \"Password\" >nul\r\n"
                        "if not errorlevel 1 (\r\n"
                        "echo %SYNTRA_GIT_TOKEN%\r\n"
                        "exit /b 0\r\n"
                        ")\r\n"
                    )

                environment["GIT_ASKPASS"] = askpass_path
                environment["SYNTRA_GIT_TOKEN"] = access_token

            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    env=environment,
                )

            except FileNotFoundError:
                raise RuntimeError(
                    "Git is not installed or not available in PATH"
                )

            if result.returncode != 0:
                print(
                    "[Repository] Clone failed"
                )

                error_message = (
                    result.stderr.strip()
                    or "Failed to clone repository"
                )

                shutil.rmtree(
                    temp_parent,
                    ignore_errors=True,
                )

                raise RuntimeError(
                    error_message
                )

            print(
                "[Repository] Clone completed successfully"
            )

            return temp_dir

        except subprocess.TimeoutExpired:
            print(
                "[Repository] Clone timed out"
            )

            shutil.rmtree(
                temp_parent,
                ignore_errors=True,
            )

            raise RuntimeError(
                "Repository cloning timed out after 60 seconds"
            )

        except Exception:
            if os.path.exists(temp_parent):
                shutil.rmtree(
                    temp_parent,
                    ignore_errors=True,
                )

            raise

        finally:
            if askpass_path and os.path.exists(
                askpass_path
            ):
                try:
                    os.remove(askpass_path)
                except OSError:
                    pass

    @staticmethod
    def cleanup_repository(
        repository_path: str,
    ) -> None:

        if (
            repository_path
            and os.path.exists(repository_path)
        ):
            print(
                "[Repository] Cleaning up "
                "temporary repository"
            )

            shutil.rmtree(
                os.path.dirname(repository_path),
                ignore_errors=True,
            )