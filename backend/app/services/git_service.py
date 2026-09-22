import base64
import os
import re
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
    def get_current_branch(
        cls,
        repository_path: str,
    ) -> dict:

        return cls.run_git(
            repository_path,
            ["branch", "--show-current"],
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

        branch_name = cls._sanitize_branch_name(
            branch_name
        )

        if not branch_name:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": "Invalid branch name",
                "command": "",
            }

        validation = cls.run_git(
            repository_path,
            [
                "check-ref-format",
                "--branch",
                branch_name,
            ],
        )

        if not validation["success"]:
            return {
                **validation,
                "stderr": (
                    validation["stderr"]
                    or "Invalid Git branch name"
                ),
            }

        existing = cls.run_git(
            repository_path,
            [
                "rev-parse",
                "--verify",
                f"refs/heads/{branch_name}",
            ],
        )

        if existing["success"]:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Branch already exists: {branch_name}",
                "command": "",
            }

        return cls.run_git(
            repository_path,
            ["checkout", "-b", branch_name],
        )

    @classmethod
    def commit_changes(
        cls,
        repository_path: str,
        message: str,
        file_paths: list[str] | None = None,
    ) -> dict:

        if not message.strip():
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": "Commit message cannot be empty",
                "command": "",
            }

        if file_paths:
            add_args = ["add", "--", *file_paths]
        else:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": (
                    "Explicit file paths are required for safe commits"
                ),
                "command": "",
            }

        add_result = cls.run_git(
            repository_path,
            add_args,
        )

        if not add_result["success"]:
            return add_result

        commit_result = cls.run_git(
            repository_path,
            ["commit", "-m", message],
        )

        if not commit_result["success"]:
            return commit_result

        sha_result = cls.run_git(
            repository_path,
            ["rev-parse", "HEAD"],
        )

        if not sha_result["success"]:
            return {
                **commit_result,
                "stderr": (
                    commit_result["stderr"]
                    or sha_result["stderr"]
                ),
                "success": False,
            }

        return {
            **commit_result,
            "stdout": f"commit {sha_result['stdout']}",
        }
    @classmethod
    def push_branch(
        cls,
        repository_path: str,
        branch_name: str,
        access_token: str | None = None,
    ) -> dict:

        if not branch_name.strip():
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": "Branch name cannot be empty",
                "command": "",
            }

        return cls.run_git(
            repository_path,
            ["push", "origin", branch_name],
            access_token=access_token,
        )

    @staticmethod
    def _sanitize_branch_name(
        branch_name: str,
    ) -> str:

        branch_name = branch_name.strip()

        branch_name = re.sub(
            r"[^A-Za-z0-9._/-]+",
            "-",
            branch_name,
        )

        branch_name = re.sub(
            r"-+",
            "-",
            branch_name,
        )

        branch_name = branch_name.strip(
            "-./"
        )

        return branch_name