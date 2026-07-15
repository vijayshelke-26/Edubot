"""
Shared pytest fixtures for the EduBot backend test suite.

The whole suite is hermetic:
  * a throwaway SQLite database (env set BEFORE app/config import),
  * the Gemini LLM forced OFF so every chat/quiz response is the
    deterministic retrieval-based fallback (no network, no API key needed).
"""
import os
import sys
import tempfile
import uuid

# --- Hermetic environment (must be set before importing app/config) ---------
_TMP_DB_FD, _TMP_DB_PATH = tempfile.mkstemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB_PATH}"
os.environ["JWT_SECRET"] = "test-secret"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest  # noqa: E402
from app import create_app  # noqa: E402
from models import db as _db  # noqa: E402


@pytest.fixture(scope="session")
def app():
    application = create_app()
    application.config.update(TESTING=True)
    yield application
    with application.app_context():
        _db.session.remove()
    try:
        os.close(_TMP_DB_FD)
        os.remove(_TMP_DB_PATH)
    except OSError:
        pass


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def _disable_llm(monkeypatch):
    """Force deterministic, offline retrieval responses for every test."""
    import nlp.response_selector as rs
    import nlp.llm_generator as llm
    monkeypatch.setattr(rs, "llm_available", lambda: False)
    monkeypatch.setattr(llm, "is_available", lambda: False)


@pytest.fixture()
def auth(client):
    """Register a fresh, unique user. Returns (auth_headers, user_dict)."""
    uname = "u" + uuid.uuid4().hex[:8]
    res = client.post(
        "/api/auth/register",
        json={"username": uname, "email": f"{uname}@example.com", "password": "secret12"},
    )
    assert res.status_code == 201, res.get_data(as_text=True)
    data = res.get_json()
    return {"Authorization": f"Bearer {data['token']}"}, data["user"]
