"""Threads publisher (Meta Threads API).

Two-step publish: create a media container then publish it.
  * Text   → single TEXT container.
  * 1 image / 1 video → single IMAGE / VIDEO container (poll until ready).
  * N media → one item container per asset (``is_carousel_item=true``), then a
    CAROUSEL container referencing their ids.

Image/video containers process asynchronously, so we poll status before publish.
"""

from __future__ import annotations

import asyncio

import httpx

from app.models import Platform
from app.publishers.base import (
    MediaItem,
    PublishError,
    PublishRequest,
    PublishResult,
    request_or_raise,
    validate_media,
)

GRAPH_BASE = "https://graph.threads.net/v1.0"
TIMEOUT = httpx.Timeout(60.0)
MEDIA_POLL_ATTEMPTS = 10
MEDIA_POLL_DELAY = 3.0  # seconds


class ThreadsPublisher:
    platform = Platform.threads

    async def publish(
        self, account_id: str, access_token: str, request: PublishRequest
    ) -> PublishResult:
        validate_media(self.platform, request.media)
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            if len(request.media) > 1:
                creation_id = await self._create_carousel(client, account_id, access_token, request)
            else:
                creation_id = await self._create_single(client, account_id, access_token, request)
                if request.media:
                    await self._await_media_ready(client, creation_id, access_token)

            published = await self._publish_container(client, account_id, access_token, creation_id)

        post_id = published.get("id")
        if not post_id:
            raise PublishError(f"Threads publish response missing id: {published}")
        return PublishResult(platform_post_id=str(post_id), raw=published)

    # ── container creation ──────────────────────────────────────────────────
    def _media_params(self, item: MediaItem) -> dict[str, str]:
        if item.kind == "video":
            return {"media_type": "VIDEO", "video_url": item.url}
        return {"media_type": "IMAGE", "image_url": item.url}

    async def _create_single(self, client, account_id, access_token, request) -> str:
        params: dict[str, str] = {"text": request.body, "access_token": access_token}
        if request.media:
            params.update(self._media_params(request.media[0]))
        else:
            params["media_type"] = "TEXT"
        resp = await self._post(client, f"{GRAPH_BASE}/{account_id}/threads", params)
        return self._require_id(resp, "container")

    async def _create_carousel(self, client, account_id, access_token, request) -> str:
        child_ids: list[str] = []
        for item in request.media:
            params = {"is_carousel_item": "true", "access_token": access_token, **self._media_params(item)}
            resp = await self._post(client, f"{GRAPH_BASE}/{account_id}/threads", params)
            child_id = self._require_id(resp, "carousel item")
            await self._await_media_ready(client, child_id, access_token)
            child_ids.append(child_id)

        params = {
            "media_type": "CAROUSEL",
            "children": ",".join(child_ids),
            "text": request.body,
            "access_token": access_token,
        }
        resp = await self._post(client, f"{GRAPH_BASE}/{account_id}/threads", params)
        return self._require_id(resp, "carousel container")

    async def _await_media_ready(self, client, creation_id: str, access_token: str) -> None:
        url = f"{GRAPH_BASE}/{creation_id}"
        for _ in range(MEDIA_POLL_ATTEMPTS):
            resp = await self._get(client, url, {"fields": "status", "access_token": access_token})
            status = resp.json().get("status")
            if status == "FINISHED":
                return
            if status in {"ERROR", "EXPIRED"}:
                raise PublishError(f"Threads media container {status}", retryable=False)
            await asyncio.sleep(MEDIA_POLL_DELAY)
        raise PublishError("Threads media container not ready in time", retryable=True)

    async def _publish_container(self, client, account_id, access_token, creation_id: str) -> dict:
        resp = await self._post(
            client,
            f"{GRAPH_BASE}/{account_id}/threads_publish",
            {"creation_id": creation_id, "access_token": access_token},
        )
        return resp.json()

    # ── helpers ───────────────────────────────────────────────────────────
    @staticmethod
    def _require_id(resp: httpx.Response, label: str) -> str:
        cid = resp.json().get("id")
        if not cid:
            raise PublishError(f"Threads {label} response missing id: {resp.text}")
        return str(cid)

    async def _post(self, client: httpx.AsyncClient, url: str, params: dict) -> httpx.Response:
        return await request_or_raise(client, "POST", url, label="Threads", params=params)

    async def _get(self, client: httpx.AsyncClient, url: str, params: dict) -> httpx.Response:
        return await request_or_raise(client, "GET", url, label="Threads", params=params)
