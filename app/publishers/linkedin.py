"""LinkedIn publisher (Posts API + Images/Videos upload APIs).

- Text → ``POST /rest/posts`` with ``commentary``.
- Image(s) → for each: ``images?action=initializeUpload`` → ``PUT`` the bytes to
  the returned ``uploadUrl`` → reference the image URN in the post
  (``content.media`` for one, ``content.multiImage`` for several).
- Video → ``videos?action=initializeUpload`` (with file size) → ``PUT`` each
  byte-range chunk, collecting ETags → ``videos?action=finalizeUpload`` → post
  with ``content.media``.

``account_id`` is the author URN (``urn:li:person:…`` / ``urn:li:organization:…``).
Bytes are fetched over HTTP from each asset's public URL.
"""

from __future__ import annotations

import httpx

from app.config import settings
from app.models import Platform
from app.publishers.base import (
    MediaItem,
    PublishError,
    PublishRequest,
    PublishResult,
    request_or_raise,
    validate_media,
)

REST_BASE = "https://api.linkedin.com/rest"
TIMEOUT = httpx.Timeout(120.0)


class LinkedInPublisher:
    platform = Platform.linkedin

    async def publish(
        self, account_id: str, access_token: str, request: PublishRequest
    ) -> PublishResult:
        validate_media(self.platform, request.media)
        headers = self._headers(access_token)

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            content: dict | None = None
            videos = [m for m in request.media if m.kind == "video"]
            images = [m for m in request.media if m.kind == "image"]

            if videos:
                urn = await self._upload_video(client, headers, account_id, videos[0])
                content = {"media": {"id": urn}}
            elif len(images) == 1:
                urn = await self._upload_image(client, headers, account_id, images[0])
                content = {"media": {"id": urn}}
            elif images:
                urns = [await self._upload_image(client, headers, account_id, m) for m in images]
                content = {"multiImage": {"images": [{"id": u} for u in urns]}}

            return await self._create_post(client, headers, account_id, request.body, content)

    # ── post creation ───────────────────────────────────────────────────────
    async def _create_post(self, client, headers, author, commentary, content) -> PublishResult:
        body: dict = {
            "author": author,
            "commentary": commentary,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        if content:
            body["content"] = content

        resp = await self._send(client, "POST", f"{REST_BASE}/posts", headers=headers, json=body)
        post_urn = resp.headers.get("x-restli-id") or resp.headers.get("x-linkedin-id")
        if not post_urn:
            raise PublishError(f"LinkedIn response missing post URN; headers={dict(resp.headers)}")
        return PublishResult(platform_post_id=post_urn, raw={"headers": dict(resp.headers)})

    # ── image upload ──────────────────────────────────────────────────────
    async def _upload_image(self, client, headers, owner, item: MediaItem) -> str:
        init = await self._send(
            client,
            "POST",
            f"{REST_BASE}/images?action=initializeUpload",
            headers=headers,
            json={"initializeUploadRequest": {"owner": owner}},
        )
        value = init.json().get("value", {})
        upload_url, urn = value.get("uploadUrl"), value.get("image")
        if not upload_url or not urn:
            raise PublishError(f"LinkedIn image init missing fields: {init.text}")

        data = await self._fetch_bytes(client, item.url)
        await self._send(
            client, "PUT", upload_url,
            headers={"Authorization": headers["Authorization"]}, content=data,
        )
        return urn

    # ── video upload (chunked) ────────────────────────────────────────────
    async def _upload_video(self, client, headers, owner, item: MediaItem) -> str:
        data = await self._fetch_bytes(client, item.url)
        init = await self._send(
            client,
            "POST",
            f"{REST_BASE}/videos?action=initializeUpload",
            headers=headers,
            json={
                "initializeUploadRequest": {
                    "owner": owner,
                    "fileSizeBytes": len(data),
                    "uploadCaptions": False,
                    "uploadThumbnail": False,
                }
            },
        )
        value = init.json().get("value", {})
        urn, upload_token = value.get("video"), value.get("uploadToken", "")
        instructions = value.get("uploadInstructions", [])
        if not urn or not instructions:
            raise PublishError(f"LinkedIn video init missing fields: {init.text}")

        part_ids: list[str] = []
        for inst in instructions:
            first, last = int(inst.get("firstByte", 0)), int(inst.get("lastByte", len(data) - 1))
            chunk = data[first : last + 1]
            put = await self._send(
                client, "PUT", inst["uploadUrl"],
                headers={"Authorization": headers["Authorization"]}, content=chunk,
            )
            etag = put.headers.get("etag") or put.headers.get("ETag")
            if not etag:
                raise PublishError("LinkedIn video chunk upload missing ETag")
            part_ids.append(etag)

        await self._send(
            client,
            "POST",
            f"{REST_BASE}/videos?action=finalizeUpload",
            headers=headers,
            json={
                "finalizeUploadRequest": {
                    "video": urn,
                    "uploadToken": upload_token,
                    "uploadedPartIds": part_ids,
                }
            },
        )
        return urn

    # ── helpers ───────────────────────────────────────────────────────────
    def _headers(self, access_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": settings.linkedin_api_version,
        }

    async def _fetch_bytes(self, client: httpx.AsyncClient, url: str) -> bytes:
        resp = await request_or_raise(client, "GET", url, label=f"media fetch {url}")
        return resp.content

    async def _send(self, client, method, url, **kwargs) -> httpx.Response:
        return await request_or_raise(client, method, url, label="LinkedIn", **kwargs)
