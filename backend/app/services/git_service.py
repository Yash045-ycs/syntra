import base64
import os
import subprocess


class GitService:

    @staticmethod
    def run_git(
        repository_path: str,
        args: list,
        access_token: str | None = None,
    ) -> dict:

        command = [
            "git",
            "-c",
            "credential.helper=",
        ] + args

        environment = {
            **os.environ,
            "GIT_TERMINAL_PROMPT": "0",
        }

        if access_token:
            credentials = base64.b64encode(
                f"x-access-token:{access_token}".encode()
            ).decode()

            environment["GIT_CONFIG_COUNT"] = "1"
            environment["GIT_CONFIG_KEY_0"] = "http.extraheader"
            environment["GIT_CONFIG_VALUE_0"] = (
                f"Authorization: Basic {credentials}"
            )

        try:
            result = subprocess.run(
                command,
                cwd=repository_path,
                capture_output=True,
                text=True,
                timeout=60,
                env=environment,
            )

            return {
                "command": " ".join(command),
                "exit_code": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "success": result.returncode == 0,
            }

        except subprocess.TimeoutExpired:
            return {
                "command": " ".join(command),
                "exit_code": -1,
                "stdout": "",
                "stderr": "Git command timed out after 60 seconds",
                "success": False,
            }

        except FileNotFoundError:
            return {
                "command": " ".join(command),
                "exit_code": -1,
                "stdout": "",
                "stderr": "Git is not installed or not available in PATH",
                "success": False,
            }

    @classmethod
    def get_status(
        cls,
        repository_path: str,
    ) -> dict:

        return cls.run_git(
            repository_path,
            ["status", "--short"],
        )

    @classmethod
    def get_diff(
        cls,
        repository_path: str,
    ) -> dict:

        return cls.run_git(
            repository_path,
            ["diff"],
        )

    @classmethod
    def create_branch(
        cls,
        repository_path: str,
        branch_name: str,
    ) -> dict:

        return cls.run_git(
            repository_path,
            ["checkout", "-b", branch_name],
        )

    @classmethod
    def commit_changes(
        cls,
        repository_path: str,
        message: str,
    ) -> dict:

        add_result = cls.run_git(
            repository_path,
            ["add", "-A"],
        )

        if not add_result["success"]:
            return add_result

        return cls.run_git(
            repository_path,
            ["commit", "-m", message],
        )

    @classmethod
    def push_branch(
        cls,
        repository_path: str,
        branch_name: str,
        access_token: str | None = None,
    ) -> dict:

        return cls.run_git(
            repository_path,
            ["push", "origin", branch_name],
            access_token=access_token,
        )