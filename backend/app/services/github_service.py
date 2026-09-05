import requests

from app.core.config import settings


class GitHubService:

    BASE_URL = "https://api.github.com"

    @classmethod
    def get_headers(cls, access_token: str | None = None) -> dict:
        token = access_token or settings.GITHUB_TOKEN

        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2026-03-10",
        }

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