"""Facebook OAuth → never-expiring Page tokens.

Flow: user login (short-lived user token) → exchange for a long-lived user
token → call ``/me/accounts`` to list managed Pages. Page tokens derived from a
long-lived user token do not expire, so each Page becomes a ConnectedAccount
with no refresh needed.
"""

from __future__ import annotations

from urllib.parse import urlencode

import httpx

from app.config import settings
from app.models import Platform, SocialAccount
from app.oauth.base import ConnectedAccount, OAuthError, RefreshedToken, oauth_request

TIMEOUT = httpx.Timeout(30.0)


class FacebookOAuth:
    platform = Platform.facebook

    @property
    def is_configured(self) -> bool:
        return bool(settings.meta_app_id and settings.meta_app_secret)

    @property
    def _base(self) -> str:
        return f"https://graph.facebook.com/{settings.facebook_graph_version}"

    def authorize_url(self, state: str) -> str:
        params = {
            "client_id": settings.meta_app_id,
            "redirect_uri": settings.redirect_uri("facebook"),
            "state": state,
            "scope": ",".join(settings.facebook_scope_list),
            "response_type": "code",
        }
        return (
            f"https://www.facebook.com/{settings.facebook_graph_version}"
            f"/dialog/oauth?{urlencode(params)}"
        )

    async def complete(self, code: str) -> list[ConnectedAccount]:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            short = await self._get(
                client,
                f"{self._base}/oauth/access_token",
                {
                    "client_id": settings.meta_app_id,
                    "client_secret": settings.meta_app_secret,
                    "redirect_uri": settings.redirect_uri("facebook"),
                    "code": code,
                },
            )
            short_token = short["access_token"]

            long = await self._get(
                client,
                f"{self._base}/oauth/access_token",
                {
                    "grant_type": "fb_exchange_token",
                    "client_id": settings.meta_app_id,
                    "client_secret": settings.meta_app_secret,
                    "fb_exchange_token": short_token,
                },
            )
            long_token = long["access_token"]

            pages = await self._get(
                client,
                f"{self._base}/me/accounts",
                {"access_token": long_token, "fields": "id,name,access_token"},
            )

        accounts: list[ConnectedAccount] = []
        for page in pages.get("data", []):
            page_token = page.get("access_token")
            if not page_token:
                continue
            accounts.append(
                ConnectedAccount(
                    platform=Platform.facebook,
                    platform_account_id=str(page["id"]),
                    display_name=page.get("name", page["id"]),
                    access_token=page_token,  # never-expiring Page token
                    refresh_token=None,
                    token_expires_at=None,
                )
            )
        if not accounts:
            raise OAuthError(
                "No manageable Facebook Pages were returned. Ensure the account "
                "manages at least one Page and granted pages_manage_posts."
            )
        return accounts

    async def refresh(self, account: SocialAccount) -> RefreshedToken | None:
        # Page tokens from a long-lived user token do not expire.
        return None

    async def verify(self, account_id: str, token: str) -> str | None:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            data = await self._get(
                client,
                f"{self._base}/{account_id}",
                {"fields": "name", "access_token": token},
            )
        return data.get("name")

    async def _get(self, client: httpx.AsyncClient, url: str, params: dict) -> dict:
        return await oauth_request(client, "GET", url, label="Facebook OAuth", params=params)
