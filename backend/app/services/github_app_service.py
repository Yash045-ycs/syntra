import time
from pathlib import Path

import jwt
import requests

from app.core.config import settings


class GitHubAppService:

    BASE_URL = "https://api.github.com"

    @classmethod
    def generate_app_jwt(cls) -> str:
        key_path = Path(settings.GITHUB_APP_PRIVATE_KEY_PATH)

        if not key_path.is_absolute():
            key_path = Path.cwd() / key_path

        if not key_path.exists():
            raise RuntimeError(
                f"GitHub App private key not found: {key_path}"
            )

        private_key = key_path.read_text(
            encoding="utf-8"
        )

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
    def generate_installation_token(
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
                "Failed to generate GitHub installation token: "
                f"{response.status_code} "
                f"{response.text}"
            )

        data = response.json()

        token = data.get("token")

        if not token:
            raise RuntimeError(
                "GitHub did not return an installation token"
            )

        return token

    @classmethod
    def get_installation_token_for_user(
        cls,
        user,
    ) -> str:

        installation_id = user.github_installation_id

        if not installation_id:
            raise RuntimeError(
                "GitHub App is not installed"
            )

        return cls.generate_installation_token(
            installation_id
        )