"""Storage backend selection + local round-trip + S3 URL building."""

from __future__ import annotations

from app.config import settings
from app.storage import LocalStorage, S3Storage, get_storage, new_key


def test_local_storage_round_trip(tmp_path):
    store = LocalStorage(str(tmp_path), "https://example.com")
    key = new_key("image/png")
    url = store.save(b"\x89PNG-bytes", key, "image/png")
    assert url == f"https://example.com/media/{key}"
    assert key.endswith(".png")
    assert store.read(key) == b"\x89PNG-bytes"
    store.delete(key)
    assert not (tmp_path / key).exists()


def test_get_storage_defaults_to_local(monkeypatch):
    monkeypatch.setattr(settings, "s3_bucket", "")
    get_storage.cache_clear()
    try:
        assert isinstance(get_storage(), LocalStorage)
    finally:
        get_storage.cache_clear()


def test_s3_public_url_builders(monkeypatch):
    monkeypatch.setattr(settings, "s3_bucket", "my-bucket")
    monkeypatch.setattr(settings, "s3_region", "eu-west-1")
    monkeypatch.setattr(settings, "s3_endpoint_url", "")
    monkeypatch.setattr(settings, "s3_public_base_url", "")
    get_storage.cache_clear()
    try:
        store = get_storage()
        assert isinstance(store, S3Storage)
        assert store._public_url("abc.jpg") == "https://my-bucket.s3.eu-west-1.amazonaws.com/abc.jpg"
        monkeypatch.setattr(settings, "s3_public_base_url", "https://cdn.example.com")
        assert store._public_url("abc.jpg") == "https://cdn.example.com/abc.jpg"
    finally:
        get_storage.cache_clear()
