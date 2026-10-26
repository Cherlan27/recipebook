from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import migrate
from app.main import create_app

FAILING_SCRIPTS = Path(__file__).parent / "fixtures" / "migrations_failing"


def test_failing_migration_prevents_application_start(monkeypatch, tmp_path):
    monkeypatch.setattr("app.db.session.settings.database_path", tmp_path / "app.db")
    monkeypatch.setattr(migrate, "DEFAULT_SCRIPT_LOCATION", FAILING_SCRIPTS)

    with pytest.raises(RuntimeError) as exc_info:
        with TestClient(create_app()):
            pytest.fail("the application must not start serving requests")

    assert "Database migration failed" in str(exc_info.value)
    assert "boom from fixture revision r2" in str(exc_info.value)
