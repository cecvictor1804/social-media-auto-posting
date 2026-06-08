"""OAuth browser-redirect routes (not under /api — the browser navigates here)."""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.api.deps import CurrentUser, DBSession
from app.models import Platform
from app.oauth import OAuthError, get_oauth_provider
from app.services import upsert_social_account

router = APIRouter(tags=["oauth"])


@router.get("/oauth/{platform}/start")
def oauth_start(platform: Platform, request: Request, user: CurrentUser):
    provider = get_oauth_provider(platform)
    if not provider.is_configured:
        return RedirectResponse(f"/accounts?error={platform.value}+not+configured", status_code=303)
    state = secrets.token_urlsafe(24)
    request.session[f"oauth_state_{platform.value}"] = state
    return RedirectResponse(provider.authorize_url(state), status_code=303)


@router.get("/oauth/{platform}/callback")
async def oauth_callback(
    platform: Platform,
    request: Request,
    user: CurrentUser,
    session: DBSession,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    if error:
        return RedirectResponse(f"/accounts?error={error}", status_code=303)
    expected = request.session.pop(f"oauth_state_{platform.value}", None)
    if not code or not state or state != expected:
        return RedirectResponse("/accounts?error=invalid+oauth+state", status_code=303)

    provider = get_oauth_provider(platform)
    try:
        connected = await provider.complete(code)
    except OAuthError as exc:
        return RedirectResponse(f"/accounts?error={exc}", status_code=303)

    for acc in connected:
        upsert_social_account(session, acc)
    return RedirectResponse("/accounts?connected=1", status_code=303)
