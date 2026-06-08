"""Media storage backends.

Uploaded images/videos are stored either in S3 (production) or on local disk
(automatic fallback when ``S3_BUCKET`` is unset, so dev and tests work without
cloud credentials). Publishers never touch this module — they only ever receive
the resulting **public URL** and fetch bytes over HTTP when a platform needs the
raw file. The single coupling point is the upload endpoint + the scheduler,
which read/write through ``get_storage()``.
"""

from __future__ import annotations

import uuid
from functools import lru_cache
from pathlib import Path
from typing import Protocol

from app.config import settings

# Map a content-type to a file extension for nicer object keys.
_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
}


def new_key(content_type: str) -> str:
    return f"{uuid.uuid4().hex}{_EXT.get(content_type, '')}"


class Storage(Protocol):
    def save(self, data: bytes, key: str, content_type: str) -> str:
        """Persist ``data`` under ``key`` and return its public URL."""
        ...

    def read(self, key: str) -> bytes: ...

    def delete(self, key: str) -> None: ...


class LocalStorage:
    """Disk-backed fallback; files are served by the app at /media/<key>."""

    def __init__(self, directory: str, public_base: str) -> None:
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.public_base = public_base.rstrip("/")

    def save(self, data: bytes, key: str, content_type: str) -> str:
        (self.dir / key).write_bytes(data)
        return f"{self.public_base}/media/{key}"

    def read(self, key: str) -> bytes:
        return (self.dir / key).read_bytes()

    def delete(self, key: str) -> None:
        (self.dir / key).unlink(missing_ok=True)


class S3Storage:
    """S3 / S3-compatible object storage (boto3)."""

    def __init__(self) -> None:
        import boto3  # imported lazily so the dep is optional for local dev

        kwargs: dict = {"region_name": settings.s3_region}
        if settings.s3_endpoint_url:
            kwargs["endpoint_url"] = settings.s3_endpoint_url
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            kwargs["aws_access_key_id"] = settings.aws_access_key_id
            kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
        self.client = boto3.client("s3", **kwargs)
        self.bucket = settings.s3_bucket

    def _public_url(self, key: str) -> str:
        if settings.s3_public_base_url:
            return f"{settings.s3_public_base_url.rstrip('/')}/{key}"
        if settings.s3_endpoint_url:
            return f"{settings.s3_endpoint_url.rstrip('/')}/{self.bucket}/{key}"
        return f"https://{self.bucket}.s3.{settings.s3_region}.amazonaws.com/{key}"

    def save(self, data: bytes, key: str, content_type: str) -> str:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        return self._public_url(key)

    def read(self, key: str) -> bytes:
        return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)


@lru_cache
def get_storage() -> Storage:
    if settings.s3_bucket:
        return S3Storage()
    return LocalStorage(settings.media_local_dir, settings.app_base_url)
