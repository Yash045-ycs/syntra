import secrets

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.db.models import GitHubOAuthState, User
from app.services.github_auth_service import GitHubAuthService
from app.services.token_encryption_service import TokenEncryptionService


router = APIRouter(
    prefix="/github",
    tags=["GitHub"],
)


@router.get("/login")
def github_login(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    state = secrets.token_urlsafe(32)

    oauth_state = GitHubOAuthState(
        state=state,
        user_id=current_user.id,
    )

    db.add(oauth_state)
    db.commit()

    authorization_url = (
        GitHubAuthService.get_authorization_url(state)
    )

    return {
        "authorization_url": authorization_url
    }


@router.get("/callback")
def github_callback(
    code: str,
    state: str | None = None,
    installation_id: int | None = None,
    setup_action: str | None = None,
    db: Session = Depends(get_db),
):
    oauth_state = None
    user = None

    if state:
        oauth_state = db.scalar(
            select(GitHubOAuthState).where(
                GitHubOAuthState.state == state
            )
        )

        if oauth_state is None:
            return RedirectResponse(
                "http://localhost:5173/github?error=invalid_state"
            )

        user = db.get(
            User,
            oauth_state.user_id,
        )

        if user is None:
            db.delete(oauth_state)
            db.commit()

            return RedirectResponse(
                "http://localhost:5173/github?error=user_not_found"
            )

        db.delete(oauth_state)
        db.commit()

    try:
        access_token = (
            GitHubAuthService.exchange_code(code)
        )

        github_user = (
            GitHubAuthService.get_user(access_token)
        )

        if user is None:
            user = db.scalar(
                select(User).where(
                    User.github_user_id
                    == github_user["id"]
                )
            )

            if user is None:
                return RedirectResponse(
                    "http://localhost:5173/github?error=account_not_linked"
                )

        existing_github_user = db.scalar(
            select(User).where(
                User.github_user_id
                == github_user["id"]
            )
        )

        if (
            existing_github_user is not None
            and existing_github_user.id != user.id
        ):
            return RedirectResponse(
                "http://localhost:5173/github?error=github_already_linked"
            )

        user.github_user_id = github_user["id"]
        user.github_username = github_user["login"]
        user.github_access_token = (
            TokenEncryptionService.encrypt(
                access_token
            )
        )

        if installation_id is not None:
            user.github_installation_id = installation_id

        db.commit()
        db.refresh(user)

        return RedirectResponse(
            "http://localhost:5173/github?connected=true"
        )

    except RuntimeError:
        return RedirectResponse(
            "http://localhost:5173/github?error=github_authorization_failed"
        )