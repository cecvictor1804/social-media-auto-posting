"""Media upload endpoint: auth, storage, validation."""

from __future__ import annotations

from app.config import settings


def test_upload_requires_auth(client, tmp_storage):
    r = client.post("/api/media", files={"file": ("a.png", b"x", "image/png")})
    assert r.status_code == 401


def test_upload_image_creates_asset(auth_client, tmp_storage):
    r = auth_client.post("/api/media", files={"file": ("a.png", b"\x89PNG-data", "image/png")})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["kind"] == "image"
    assert data["content_type"] == "image/png"
    assert "/media/" in data["url"]
    # The file actually landed in the temp storage dir.
    assert any(tmp_storage.iterdir())


def test_upload_rejects_unsupported_type(auth_client, tmp_storage):
    r = auth_client.post("/api/media", files={"file": ("a.txt", b"hi", "text/plain")})
    assert r.status_code == 400


def test_upload_rejects_oversize(auth_client, tmp_storage, monkeypatch):
    monkeypatch.setattr(settings, "media_max_image_mb", 0)  # any non-empty file is too big
    r = auth_client.post("/api/media", files={"file": ("a.png", b"larger-than-zero", "image/png")})
    assert r.status_code == 400
    assert "too large" in r.json()["detail"].lower()
