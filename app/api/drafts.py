"""Compose metadata + AI drafting routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.ai import DraftError, DraftRequest, available_models, draft_posts
from app.api.deps import CurrentUser, DBSession
from app.config import settings
from app.publishers.base import PLATFORM_CHAR_LIMITS
from app.schemas import DraftItemOut, DraftRequestIn, MetaOut, ModelOut, platform_meta
from app.services import active_accounts

router = APIRouter(prefix="/api", tags=["compose"])


@router.get("/meta", response_model=MetaOut)
def meta(user: CurrentUser):
    return MetaOut(
        models=[
            ModelOut(id=m.id, label=m.label, provider=m.provider.value)
            for m in available_models()
        ],
        default_model=settings.default_ai_model,
        tones=["professional", "casual", "enthusiastic", "informative", "witty"],
        platforms=platform_meta(),
    )


@router.post("/drafts/ai", response_model=list[DraftItemOut])
async def generate_drafts(payload: DraftRequestIn, user: CurrentUser, session: DBSession):
    brief = payload.brief.strip()
    accounts = [a for a in active_accounts(session) if a.id in payload.account_ids]
    if not brief or not accounts:
        raise HTTPException(
            status_code=400, detail="Enter a brief and select at least one account."
        )

    platforms = list({a.platform for a in accounts})
    model = payload.model or settings.default_ai_model
    try:
        drafts = await draft_posts(
            DraftRequest(brief=brief, platforms=platforms, tone=payload.tone, model=model)
        )
    except DraftError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return [
        DraftItemOut(
            account_id=a.id,
            platform=a.platform.value,
            display_name=a.display_name,
            body=drafts.get(a.platform, ""),
            limit=PLATFORM_CHAR_LIMITS[a.platform],
        )
        for a in accounts
    ]
