import requests

from app.core.config import settings


class GitHubAuthService:

    AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    API_URL = "https://api.github.com"

    @classmethod
    def get_authorization_url(cls, state: str) -> str:
        params = {
    "client_id": settings.GITHUB_CLIENT_ID,
    "redirect_uri": "http://localhost:8000/api/github/callback",
    "state": state,
    "scope": "repo read:user",
}

        query = "&".join(
            f"{key}={requests.utils.quote(str(value))}"
            for key, value in params.items()
        )

        return f"{cls.AUTHORIZE_URL}?{query}"

    @classmethod
    def exchange_code(cls, code: str) -> str:
        response = requests.post(
            cls.TOKEN_URL,
            headers={
                "Accept": "application/json",
            },
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
            },
            timeout=30,
        )

        if not response.ok:
            raise RuntimeError(
                "GitHub authorization failed"
            )

        data = response.json()

        access_token = data.get("access_token")

        if not access_token:
            raise RuntimeError(
                data.get(
                    "error_description",
                    "GitHub did not return an access token",
                )
            )

        return access_token

    @classmethod
    def get_user(cls, access_token: str) -> dict:
        response = requests.get(
            f"{cls.API_URL}/user",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {access_token}",
                "X-GitHub-Api-Version": "2026-03-10",
            },
            timeout=30,
        )

        if not response.ok:
            raise RuntimeError(
                "Failed to retrieve GitHub user"
            )

        data = response.json()

        return {
            "id": data["id"],
            "login": data["login"],
            "name": data.get("name"),
            "avatar_url": data.get("avatar_url"),
        }