from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import create_app


def test_root_serves_frontend_entry_document_when_dist_exists(monkeypatch, tmp_path):
    (tmp_path / "index.html").write_text("<html>recipebook</html>")
    monkeypatch.setattr(settings, "frontend_dist", tmp_path)

    client = TestClient(create_app())
    response = client.get("/")

    assert response.status_code == 200
    assert "recipebook" in response.text


def test_health_still_reachable_when_frontend_is_mounted(monkeypatch, tmp_path):
    (tmp_path / "index.html").write_text("<html>recipebook</html>")
    monkeypatch.setattr(settings, "frontend_dist", tmp_path)

    client = TestClient(create_app())
    response = client.get("/health")

    assert response.status_code == 200


def test_app_starts_without_frontend_build(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "frontend_dist", tmp_path / "missing")

    client = TestClient(create_app())

    assert client.get("/health").status_code == 200
    assert client.get("/").status_code == 404
