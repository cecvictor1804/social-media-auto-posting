"""Facebook Page publisher (Graph API).

- Text  → ``POST /{page-id}/feed``.
- 1 image → ``POST /{page-id}/photos`` with an image ``url`` + caption.
- N images → upload each as an *unpublished* photo, then attach their ids to a
  ``/feed`` post via ``attached_media``.
- 1 video → ``POST /{page-id}/videos`` with ``file_url`` + description.

Requires a Page access token with ``pages_manage_posts``.
"""

from __future__ import annotations

import json

import httpx

from app.config import settings
from app.models import Platform
from app.publishers.base import (
    PublishError,
    PublishRequest,
    PublishResult,
    request_or_raise,
    validate_media,
)

GRAPH_BASE = "https://graph.facebook.com"
TIMEOUT = httpx.Timeout(120.0)  # video fetches can be slow


class FacebookPublisher:
    platform = Platform.facebook

    async def publish(
        self, account_id: str, access_token: str, request: PublishRequest
    ) -> PublishResult:
        validate_media(self.platform, request.media)
        version = settings.facebook_graph_version
        base = f"{GRAPH_BASE}/{version}/{account_id}"

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            videos = [m for m in request.media if m.kind == "video"]
            images = [m for m in request.media if m.kind == "image"]

            if videos:
                payload = await self._post_video(client, base, access_token, videos[0].url, request.body)
            elif len(images) == 1:
                payload = await self._post_single_photo(client, base, access_token, images[0].url, request.body)
            elif images:
                payload = await self._post_multi_photo(client, base, access_token, images, request.body)
            else:
                payload = (await self._post(client, f"{base}/feed", {"message": request.body, "access_token": access_token})).json()

        post_id = payload.get("post_id") or payload.get("id")
        if not post_id:
            raise PublishError(f"Facebook response missing post id: {payload}")
        return PublishResult(platform_post_id=str(post_id), raw=payload)

    # ── media variants ─────────────────────────────────────────────────────
    async def _post_single_photo(self, client, base, token, url, caption) -> dict:
        resp = await self._post(
            client, f"{base}/photos", {"url": url, "caption": caption, "access_token": token}
        )
        return resp.json()

    async def _post_multi_photo(self, client, base, token, images, message) -> dict:
        fbids: list[str] = []
        for img in images:
            resp = await self._post(
                client,
                f"{base}/photos",
                {"url": img.url, "published": "false", "access_token": token},
            )
            pid = resp.json().get("id")
            if not pid:
                raise PublishError(f"Facebook photo upload missing id: {resp.text}")
            fbids.append(str(pid))

        data = {"message": message, "access_token": token}
        for i, fbid in enumerate(fbids):
            data[f"attached_media[{i}]"] = json.dumps({"media_fbid": fbid})
        resp = await self._post(client, f"{base}/feed", data)
        return resp.json()

    async def _post_video(self, client, base, token, file_url, description) -> dict:
        resp = await self._post(
            client,
            f"{base}/videos",
            {"file_url": file_url, "description": description, "access_token": token},
        )
        return resp.json()

    # ── http helper ─────────────────────────────────────────────────────────
    async def _post(self, client: httpx.AsyncClient, url: str, data: dict) -> httpx.Response:
        return await request_or_raise(client, "POST", url, label="Facebook", data=data)
