from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RECIPEBOOK_")

    cors_allowed_origins: list[str] = ["http://localhost:5173"]
    database_path: Path = BACKEND_ROOT / "data" / "app.db"
    frontend_dist: Path = BACKEND_ROOT.parent / "frontend" / "dist"

    @property
    def database_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.database_path}"


settings = Settings()
