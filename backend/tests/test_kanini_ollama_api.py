from fastapi.testclient import TestClient

from app.api import kanini_resumes
from app.core.config import settings
from app.core.database import get_db_session
from app.core.security import create_access_token
from app.main import app
from app.storage import get_storage_backend
from app.storage.local import LocalStorageBackend


def _header(user) -> dict[str, str]:
    token, _, _ = create_access_token(user.id, user.role, remember_me=False)
    return {"Authorization": f"Bearer {token}"}


def test_model_options_endpoint_uses_environment(sqlite_session, user_factory, monkeypatch) -> None:
    user = user_factory()
    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    monkeypatch.setattr(settings, "ollama_base_url", "http://ollama.test")
    monkeypatch.setattr(settings, "ollama_model", "llama3.1")
    monkeypatch.setattr(settings, "ollama_models", "llama3.1,qwen3:14b")
    try:
        response = TestClient(app).get("/api/v1/kanini/llm-models", headers=_header(user))
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert [model["value"] for model in response.json()["models"]] == [
        "auto",
        "ollama:llama3.1",
        "ollama:qwen3:14b",
    ]


def test_upload_returns_pending_extraction_job(sqlite_session, user_factory, monkeypatch, tmp_path) -> None:
    user = user_factory()
    app.dependency_overrides[get_db_session] = lambda: sqlite_session
    app.dependency_overrides[get_storage_backend] = lambda: LocalStorageBackend(str(tmp_path))
    parsed_data = {
        "contact": {"name": "Asha Sharma", "email": "asha@example.com"},
        "experience": [{"title": "Engineer", "company": "Acme"}],
        "projects": [{"name": "Portal"}],
    }
    monkeypatch.setattr(kanini_resumes, "parse_resume", lambda *_args: parsed_data)
    monkeypatch.setattr(kanini_resumes, "process_resume_extraction_job", lambda *_args: None)
    try:
        response = TestClient(app).post(
            "/api/v1/kanini/upload",
            headers=_header(user),
            files={"file": ("resume.pdf", b"%PDF-test", "application/pdf")},
            data={"llm_model": "ollama:llama3.1"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["llm_requested"] == "ollama:llama3.1"
    assert body["llm_used"] is None
    assert body["extraction_status"] == "pending"
    assert body["extraction_progress"] == 5
    assert body["parsed_data"]["experience"][0]["company"] == "Acme"