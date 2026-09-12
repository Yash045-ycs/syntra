import base64
import os
import subprocess
import time

import jwt
import requests

from app.core.config import settings


class GitHubService:

    BASE_URL = "https://api.github.com"

    @classmethod
    def get_headers(
        cls,
        access_token: str | None = None,
    ) -> dict:

        token = access_token or settings.GITHUB_TOKEN

        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2026-03-10",
        }

    @classmethod
    def generate_app_jwt(cls) -> str:

        private_key_path = (
            settings.GITHUB_APP_PRIVATE_KEY_PATH
        )

        with open(
            private_key_path,
            "r",
            encoding="utf-8",
        ) as file:
            private_key = file.read()

        now = int(time.time())

        payload = {
            "iat": now - 60,
            "exp": now + 540,
            "iss": str(settings.GITHUB_APP_ID),
        }

        return jwt.encode(
            payload,
            private_key,
            algorithm="RS256",
        )

    @classmethod
    def get_installation_id(
        cls,
        owner: str,
        repository: str,
    ) -> int:

        app_jwt = cls.generate_app_jwt()

        response = requests.get(
            f"{cls.BASE_URL}/repos/"
            f"{owner}/{repository}/installation",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {app_jwt}",
                "X-GitHub-Api-Version": "2026-03-10",
            },
            timeout=30,
        )

        if not response.ok:
            raise RuntimeError(
                f"GitHub installation request failed: "
                f"{response.status_code} "
                f"{response.text}"
            )

        data = response.json()

        return data["id"]

    @classmethod
    def create_installation_token(
        cls,
        installation_id: int,
    ) -> str:

        app_jwt = cls.generate_app_jwt()

        response = requests.post(
            f"{cls.BASE_URL}/app/installations/"
            f"{installation_id}/access_tokens",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {app_jwt}",
                "X-GitHub-Api-Version": "2026-03-10",
            },
            timeout=30,
        )

        if not response.ok:
            raise RuntimeError(
                f"GitHub installation token request failed: "
                f"{response.status_code} "
                f"{response.text}"
            )

        data = response.json()

        return data["token"]

    @classmethod
    def get_repository(
        cls,
        owner: str,
        repository: str,
        access_token: str | None = None,
    ) -> dict:

        url = (
            f"{cls.BASE_URL}/repos/"
            f"{owner}/{repository}"
        )

        response = requests.get(
            url,
            headers=cls.get_headers(access_token),
            timeout=30,
        )

        if not response.ok:
            raise RuntimeError(
                f"GitHub repository request failed: "
                f"{response.status_code} "
                f"{response.text}"
            )

        data = response.json()

        return {
            "full_name": data["full_name"],
            "name": data["name"],
            "owner": data["owner"]["login"],
            "default_branch": data["default_branch"],
            "private": data["private"],
            "html_url": data["html_url"],
        }

    @classmethod
    def clone_repository(
        cls,
        repository_url: str,
        destination: str,
        access_token: str,
    ) -> dict:

        credentials = base64.b64encode(
            f"x-access-token:{access_token}".encode()
        ).decode()

        environment = {
            **os.environ,
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "http.extraheader",
            "GIT_CONFIG_VALUE_0": (
                f"Authorization: Basic {credentials}"
            ),
        }

        command = [
            "git",
            "-c",
            "credential.helper=",
            "clone",
            repository_url,
            destination,
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
                env=environment,
            )

            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": "Git clone timed out after 120 seconds",
            }

        except FileNotFoundError:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": "Git is not installed or unavailable in PATH",
            }

    @classmethod
    def create_pull_request(
        cls,
        owner: str,
        repository: str,
        title: str,
        body: str,
        head: str,
        base: str,
        access_token: str | None = None,
    ) -> dict:

        url = (
            f"{cls.BASE_URL}/repos/"
            f"{owner}/{repository}/pulls"
        )

        payload = {
            "title": title,
            "body": body,
            "head": head,
            "base": base,
        }

        response = requests.post(
            url,
            headers=cls.get_headers(access_token),
            json=payload,
            timeout=30,
        )

        if not response.ok:
            raise RuntimeError(
                f"GitHub pull request creation failed: "
                f"{response.status_code} "
                f"{response.text}"
            )

        data = response.json()

        return {
            "number": data["number"],
            "title": data["title"],
            "url": data["html_url"],
            "state": data["state"],
            "head": data["head"]["ref"],
            "base": data["base"]["ref"],
        }

    @classmethod
    def get_pull_request_files(
        cls,
        owner: str,
        repository: str,
        pull_number: int,
        access_token: str | None = None,
    ) -> list[dict]:

        url = (
            f"{cls.BASE_URL}/repos/"
            f"{owner}/{repository}/pulls/"
            f"{pull_number}/files"
        )

        response = requests.get(
            url,
            headers=cls.get_headers(access_token),
            params={
                "per_page": 100,
            },
            timeout=30,
        )

        if not response.ok:
            raise RuntimeError(
                f"GitHub pull request files request failed: "
                f"{response.status_code} "
                f"{response.text}"
            )

        data = response.json()

        return [
            {
                "filename": file.get("filename"),
                "status": file.get("status"),
                "additions": file.get("additions", 0),
                "deletions": file.get("deletions", 0),
                "changes": file.get("changes", 0),
                "patch": file.get("patch"),
            }
            for file in data
        ]

    @classmethod
    def get_pull_request(
        cls,
        owner: str,
        repository: str,
        pull_number: int,
        access_token: str | None = None,
    ) -> dict:

        url = (
            f"{cls.BASE_URL}/repos/"
            f"{owner}/{repository}/pulls/"
            f"{pull_number}"
        )

        response = requests.get(
            url,
            headers=cls.get_headers(access_token),
            timeout=30,
        )

        if not response.ok:
            raise RuntimeError(
                f"GitHub pull request request failed: "
                f"{response.status_code} "
                f"{response.text}"
            )

        data = response.json()

        return {
            "number": data["number"],
            "title": data["title"],
            "url": data["html_url"],
            "state": data["state"],
            "merged": data["merged"],
            "mergeable": data["mergeable"],
            "draft": data["draft"],
            "head": data["head"]["ref"],
            "base": data["base"]["ref"],
        }
