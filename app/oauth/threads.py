"""Threads OAuth (authorization code → long-lived token + refresh).

Flow: exchange the callback code for a short-lived token + ``user_id``, then
exchange that for a long-lived token (~60 days). Long-lived tokens are refreshed
via ``refresh_access_token`` before expiry.
"""

from __future__ import annotations

from datetime import timedelta
from urllib.parse import urlencode

import httpx

from app.config import settings
from app.models import Platform, SocialAccount, utcnow
from app.oauth.base import ConnectedAccount, OAuthError, RefreshedToken, oauth_request

AUTHORIZE_URL = "https://threads.net/oauth/authorize"
GRAPH = "https://graph.threads.net"
TIMEOUT = httpx.Timeout(30.0)


class ThreadsOAuth:
    platform = Platform.threads

    @property
    def is_configured(self) -> bool:
        return bool(settings.meta_app_id and settings.meta_app_secret)

    def authorize_url(self, state: str) -> str:
        params = {
            "client_id": settings.meta_app_id,
            "redirect_uri": settings.redirect_uri("threads"),
            "scope": ",".join(settings.threads_scope_list),
            "response_type": "code",
            "state": state,
        }
        return f"{AUTHORIZE_URL}?{urlencode(params)}"

    async def complete(self, code: str) -> list[ConnectedAccount]:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            short = await self._post(
                client,
                f"{GRAPH}/oauth/access_token",
                {
                    "client_id": settings.meta_app_id,
                    "client_secret": settings.meta_app_secret,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.redirect_uri("threads"),
                    "code": code,
                },
            )
            user_id = str(short["user_id"])

            long = await self._get(
                client,
                f"{GRAPH}/access_token",
                {
                    "grant_type": "th_exchange_token",
                    "client_secret": settings.meta_app_secret,
                    "access_token": short["access_token"],
                },
            )
            access_token = long["access_token"]
            expires_at = utcnow() + timedelta(seconds=int(long.get("expires_in", 0)))

            username = await self._username(client, user_id, access_token)

        return [
            ConnectedAccount(
                platform=Platform.threads,
                platform_account_id=user_id,
                display_name=username or f"Threads {user_id}",
                access_token=access_token,
                refresh_token=None,  # Threads refreshes the access token itself
                token_expires_at=expires_at,
            )
        ]

    async def refresh(self, account: SocialAccount) -> RefreshedToken | None:
        from app.security import decrypt_token

        current = decrypt_token(account.access_token_enc)
        if not current:
            return None
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            data = await self._get(
                client,
                f"{GRAPH}/refresh_access_token",
                {"grant_type": "th_refresh_token", "access_token": current},
            )
        expires_at = utcnow() + timedelta(seconds=int(data.get("expires_in", 0)))
        return RefreshedToken(
            access_token=data["access_token"], refresh_token=None, token_expires_at=expires_at
        )

    async def verify(self, account_id: str, token: str) -> str | None:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            data = await self._get(
                client,
                f"{GRAPH}/v1.0/{account_id}",
                {"fields": "username", "access_token": token},
            )
        return data.get("username")

    # ── helpers ──────────────────────────────────────────────────────────
    async def _username(
        self, client: httpx.AsyncClient, user_id: str, access_token: str
    ) -> str | None:
        try:
            data = await self._get(
                client,
                f"{GRAPH}/v1.0/{user_id}",
                {"fields": "username", "access_token": access_token},
            )
            return data.get("username")
        except OAuthError:
            return None

    async def _post(self, client: httpx.AsyncClient, url: str, data: dict) -> dict:
        return await oauth_request(client, "POST", url, label="Threads OAuth", data=data)

    async def _get(self, client: httpx.AsyncClient, url: str, params: dict) -> dict:
        return await oauth_request(client, "GET", url, label="Threads OAuth", params=params)
