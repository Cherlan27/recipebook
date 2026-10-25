from pathlib import Path

from app.core.config import BACKEND_ROOT, Settings


def test_database_path_uses_documented_default_when_unset(monkeypatch):
    monkeypatch.delenv("RECIPEBOOK_DATABASE_PATH", raising=False)

    settings = Settings()

    assert settings.database_path == BACKEND_ROOT / "data" / "app.db"


def test_database_path_is_overridden_by_env_var(monkeypatch, tmp_path):
    override = tmp_path / "custom" / "app.db"
    monkeypatch.setenv("RECIPEBOOK_DATABASE_PATH", str(override))

    settings = Settings()

    assert settings.database_path == Path(override)
