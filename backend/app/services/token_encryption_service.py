from cryptography.fernet import Fernet

from app.core.config import settings


class TokenEncryptionService:

    cipher = Fernet(
        settings.GITHUB_TOKEN_ENCRYPTION_KEY.encode()
    )

    @classmethod
    def encrypt(cls, token: str) -> str:
        return cls.cipher.encrypt(
            token.encode()
        ).decode()

    @classmethod
    def decrypt(cls, encrypted_token: str) -> str:
        return cls.cipher.decrypt(
            encrypted_token.encode()
        ).decode()