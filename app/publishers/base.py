"""Common publisher protocol and shared types.

Every platform publisher takes a decrypted access token + the platform account
id and a :class:`PublishRequest`, and returns a :class:`PublishResult` carrying
the platform-assigned post id. Transient failures raise ``PublishError`` with
``retryable=True`` so the scheduler can back off and retry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import httpx

from app.models import Platform

# Per-platform body length limits used for validation and AI drafting.
PLATFORM_CHAR_LIMITS: dict[Platform, int] = {
    Platform.facebook: 63206,
    Platform.linkedin: 3000,
    Platform.threads: 500,
}

# Max number of images allowed in one post per platform (video is always 1).
PLATFORM_MAX_IMAGES: dict[Platform, int] = {
    Platform.facebook: 10,
    Platform.linkedin: 20,
    Platform.threads: 20,
}


@dataclass(slots=True)
class MediaItem:
    """One attached asset, resolved to a publicly fetchable URL."""

    url: str
    content_type: str
    kind: str  # "image" | "video"


@dataclass(slots=True)
class PublishRequest:
    body: str
    media: list[MediaItem] = field(default_factory=list)


def validate_media(platform: Platform, media: list[MediaItem]) -> None:
    """Enforce the shared rule: a post is either 1..N images or exactly 1 video.

    Raises a non-retryable :class:`PublishError` on violation.
    """
    if not media:
        return
    videos = [m for m in media if m.kind == "video"]
    images = [m for m in media if m.kind == "image"]
    if videos and images:
        raise PublishError("Cannot mix images and video in one post.", retryable=False)
    if videos and len(videos) > 1:
        raise PublishError("Only one video per post is supported.", retryable=False)
    max_images = PLATFORM_MAX_IMAGES.get(platform, 1)
    if len(images) > max_images:
        raise PublishError(
            f"{platform.value} allows at most {max_images} images per post.", retryable=False
        )


@dataclass(slots=True)
class PublishResult:
    platform_post_id: str
    raw: dict | None = None


class PublishError(Exception):
    """Raised when a publish attempt fails.

    ``retryable`` distinguishes transient failures (5xx, rate limits, timeouts)
    that should be retried from permanent ones (bad request, revoked token).
    """

    def __init__(self, message: str, *, retryable: bool = False, status: int | None = None):
        super().__init__(message)
        self.retryable = retryable
        self.status = status


def is_retryable_status(status: int) -> bool:
    return status == 429 or 500 <= status < 600


async def request_or_raise(
    client: httpx.AsyncClient, method: str, url: str, *, label: str, **kwargs
) -> httpx.Response:
    """Send an HTTP request, normalizing failures into ``PublishError``.

    Transport errors are retryable; non-2xx responses use ``is_retryable_status``.
    Shared by all publishers so the error contract is identical everywhere.
    """
    try:
        resp = await client.request(method, url, **kwargs)
    except httpx.RequestError as exc:
        raise PublishError(f"{label} request error: {exc}", retryable=True) from exc
    if resp.is_success:
        return resp
    raise PublishError(
        f"{label} API {resp.status_code}: {resp.text}",
        retryable=is_retryable_status(resp.status_code),
        status=resp.status_code,
    )


class Publisher(Protocol):
    platform: Platform

    async def publish(
        self, account_id: str, access_token: str, request: PublishRequest
    ) -> PublishResult: ...
