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

# Deep-link scheme used by the Android app (must match app.json "scheme").
_MOBILE_SCHEME = "socialposter"


@router.get("/oauth/{platform}/start")
def oauth_start(platform: Platform, request: Request, user: CurrentUser):
    provider = get_oauth_provider(platform)
    if not provider.is_configured:
        return RedirectResponse(f"/accounts?error={platform.value}+not+configured", status_code=303)
    state = secrets.token_urlsafe(24)
    request.session[f"oauth_state_{platform.value}"] = state
    # mobile=1 signals the callback to redirect to the app deep-link instead of /accounts
    if request.query_params.get("mobile"):
        request.session[f"oauth_mobile_{platform.value}"] = "1"
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
    is_mobile = bool(request.session.pop(f"oauth_mobile_{platform.value}", None))

    def _redirect(path: str) -> RedirectResponse:
        """Return a web or deep-link redirect depending on the caller."""
        if is_mobile:
            return RedirectResponse(
                f"{_MOBILE_SCHEME}://oauth/callback?{path}", status_code=303
            )
        return RedirectResponse(f"/{path}", status_code=303)

    if error:
        return _redirect(f"accounts?error={error}" if not is_mobile else f"error={error}")

    expected = request.session.pop(f"oauth_state_{platform.value}", None)
    if not code or not state or state != expected:
        msg = "invalid+oauth+state"
        return _redirect(f"accounts?error={msg}" if not is_mobile else f"error={msg}")

    provider = get_oauth_provider(platform)
    try:
        connected = await provider.complete(code)
    except OAuthError as exc:
        msg = str(exc).replace(" ", "+")
        return _redirect(f"accounts?error={msg}" if not is_mobile else f"error={msg}")

    for acc in connected:
        upsert_social_account(session, acc)

    if is_mobile:
        return RedirectResponse(
            f"{_MOBILE_SCHEME}://oauth/callback?platform={platform.value}&connected=1",
            status_code=303,
        )
    return RedirectResponse("/accounts?connected=1", status_code=303)
