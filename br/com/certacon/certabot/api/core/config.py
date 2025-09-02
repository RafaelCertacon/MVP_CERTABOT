from pathlib import Path
from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "MVP Gerenciador"
    JWT_SECRET: str = "change-me-super-secret"
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_MIN: int = 60

    DATABASE_URL: str = "sqlite:///./app.db"
    UPLOAD_DIR: Path = Path("./uploads").resolve()

    class Config:
        env_file = ".env"

settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
