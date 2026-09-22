from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    GEMINI_API_KEY: str
    GITHUB_TOKEN: str
    GITHUB_APP_ID: int
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_TOKEN_ENCRYPTION_KEY: str
    GITHUB_APP_PRIVATE_KEY_PATH: str
    GITHUB_REDIRECT_URI: str

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()