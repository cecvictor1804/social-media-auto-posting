"""Common OAuth types.

Each provider exposes:
  * ``is_configured`` — whether app credentials are present.
  * ``authorize_url(state)`` — where to redirect the user to grant access.
  * ``complete(code)`` — exchange the callback ``code`` for one or more
    :class:`ConnectedAccount` records (Facebook may return several Pages).
  * ``refresh(account)`` — return a refreshed token tuple, or ``None`` if the
    platform's tokens don't need refreshing.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

import httpx

from app.models import Platform, SocialAccount


@dataclass(slots=True)
class ConnectedAccount:
    platform: Platform
    platform_account_id: str
    display_name: str
    access_token: str
    refresh_token: str | None = None
    token_expires_at: datetime | None = None


@dataclass(slots=True)
class RefreshedToken:
    access_token: str
    refresh_token: str | None
    token_expires_at: datetime | None


class OAuthError(Exception):
    pass


async def oauth_request(
    client: httpx.AsyncClient, method: str, url: str, *, label: str, **kwargs
) -> dict:
    """Send an OAuth HTTP request and return parsed JSON, raising ``OAuthError``
    on transport failure or a non-2xx response. Shared by all OAuth providers."""
    try:
        resp = await client.request(method, url, **kwargs)
    except httpx.RequestError as exc:
        raise OAuthError(f"{label} request failed: {exc}") from exc
    if not resp.is_success:
        raise OAuthError(f"{label} {resp.status_code}: {resp.text}")
    return resp.json()


@runtime_checkable
class OAuthProvider(Protocol):
    platform: Platform

    @property
    def is_configured(self) -> bool: ...

    def authorize_url(self, state: str) -> str: ...

    async def complete(self, code: str) -> list[ConnectedAccount]: ...

    async def refresh(self, account: SocialAccount) -> RefreshedToken | None: ...

    async def verify(self, account_id: str, token: str) -> str | None:
        """Check a manually-entered credential; return a display name if valid.

        Raises :class:`OAuthError` if the platform rejects the credential.
        """
        ...
