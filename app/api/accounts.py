"""Account management routes: list, manual add, disconnect."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, DBSession
from app.models import Platform, SocialAccount
from app.oauth import ConnectedAccount, OAuthError, get_oauth_provider
from app.schemas import AccountOut, ManualAccountIn
from app.services import active_accounts, upsert_social_account
from app.timeutil import parse_local_input

router = APIRouter(prefix="/api", tags=["accounts"])


@router.get("/accounts")
def accounts(user: CurrentUser, session: DBSession):
    return {
        "accounts": [AccountOut.from_orm_account(a) for a in active_accounts(session)],
        "configured": {p.value: get_oauth_provider(p).is_configured for p in Platform},
    }


@router.post("/accounts/{platform}/manual", response_model=AccountOut)
async def add_account_manual(
    platform: Platform, payload: ManualAccountIn, user: CurrentUser, session: DBSession
):
    account_id = payload.platform_account_id.strip()
    access_token = payload.access_token.strip()
    display_name = payload.display_name.strip()
    refresh_token = (payload.refresh_token or "").strip() or None

    if not account_id or not access_token:
        raise HTTPException(status_code=400, detail="Account id and access token are required.")

    expires_at = None
    raw_expiry = (payload.token_expires_at or "").strip()
    if raw_expiry:
        try:
            expires_at = (
                parse_local_input(raw_expiry)
                if "T" in raw_expiry
                else parse_local_input(raw_expiry + "T00:00")
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid expiry date.") from exc

    if payload.action == "verify":
        provider = get_oauth_provider(platform)
        try:
            verified_name = await provider.verify(account_id, access_token)
        except OAuthError as exc:
            raise HTTPException(status_code=400, detail=f"Verification failed: {exc}") from exc
        if verified_name and not display_name:
            display_name = verified_name

    account = upsert_social_account(
        session,
        ConnectedAccount(
            platform=platform,
            platform_account_id=account_id,
            display_name=display_name or f"{platform.value} account",
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=expires_at,
        ),
    )
    return AccountOut.from_orm_account(account)


@router.post("/accounts/{account_id}/disconnect")
def disconnect(account_id: int, user: CurrentUser, session: DBSession):
    account = session.get(SocialAccount, account_id)
    if account:
        account.is_active = False
        session.commit()
    return {"ok": True}
