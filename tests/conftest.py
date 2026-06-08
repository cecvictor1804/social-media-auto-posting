"""Test fixtures. Sets env BEFORE importing app modules so settings pick it up."""

from __future__ import annotations

import os

from cryptography.fernet import Fernet

# Must be set before any `app.*` import (settings is a cached singleton).
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_smap.db")
os.environ.setdefault("FERNET_KEY", Fernet.generate_key().decode())
os.environ.setdefault("SESSION_SECRET", "test-secret")
os.environ.setdefault("ANTHROPIC_API_KEY", "")  # default: no providers configured

import pytest  # noqa: E402

from app.db import Base, SessionLocal, engine  # noqa: E402
import app.models  # noqa: E402,F401  (register tables)


ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "change-me"  # matches Settings defaults used by ensure_admin


@pytest.fixture()
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(session):
    """TestClient over the app with tables created (startup bootstraps admin)."""
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_client(client):
    """A TestClient already logged in as the bootstrap admin."""
    resp = client.post("/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert resp.status_code == 200, resp.text
    return client


@pytest.fixture()
def tmp_storage(tmp_path, monkeypatch):
    """Force the local-disk storage backend into a temp dir (no S3/AWS needed)."""
    import app.storage as storage_mod
    from app.config import settings

    monkeypatch.setattr(settings, "s3_bucket", "")
    monkeypatch.setattr(settings, "media_local_dir", str(tmp_path))
    storage_mod.get_storage.cache_clear()
    try:
        yield tmp_path
    finally:
        storage_mod.get_storage.cache_clear()
