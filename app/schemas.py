"""Pydantic request/response models for the JSON API.

These are the wire contract consumed by the React SPA. Builders convert ORM
objects (returned by ``app.services``) into safe, token-free payloads. The
service layer is unchanged — schemas only shape what crosses the boundary.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MediaAsset, Platform, Post, PostTarget, SocialAccount, User
from app.publishers.base import PLATFORM_CHAR_LIMITS
from app.timeutil import utc_to_local_str

# Brand colors mirrored on the frontend (single source for non-UI consumers).
PLATFORM_BRAND: dict[str, str] = {
    "facebook": "#1877F2",
    "linkedin": "#0A66C2",
    "threads": "#000000",
}


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


# ── Auth ────────────────────────────────────────────────────────────────────
class LoginIn(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    is_admin: bool


class UserAdminOut(BaseModel):
    id: int
    email: str
    is_admin: bool
    is_active: bool
    created_at: str | None

    @classmethod
    def from_orm_user(cls, u: User) -> "UserAdminOut":
        return cls(
            id=u.id,
            email=u.email,
            is_admin=u.is_admin,
            is_active=u.is_active,
            created_at=_iso(u.created_at),
        )


class CreateUserIn(BaseModel):
    email: str
    password: str
    is_admin: bool = False


class UpdateUserIn(BaseModel):
    is_admin: bool | None = None
    is_active: bool | None = None


# ── Compose metadata ─────────────────────────────────────────────────────────
class ModelOut(BaseModel):
    id: str
    label: str
    provider: str


class PlatformMetaOut(BaseModel):
    value: str
    label: str
    color: str
    char_limit: int


class MetaOut(BaseModel):
    models: list[ModelOut]
    default_model: str
    tones: list[str]
    platforms: list[PlatformMetaOut]


# ── Accounts ──────────────────────────────────────────────────────────────────
class AccountOut(BaseModel):
    id: int
    platform: str
    display_name: str
    platform_account_id: str
    token_set: bool
    token_expires_at: str | None
    token_expires_display: str | None
    is_active: bool

    @classmethod
    def from_orm_account(cls, a: SocialAccount) -> "AccountOut":
        return cls(
            id=a.id,
            platform=a.platform.value,
            display_name=a.display_name,
            platform_account_id=a.platform_account_id,
            token_set=bool(a.access_token_enc),
            token_expires_at=_iso(a.token_expires_at),
            token_expires_display=(
                utc_to_local_str(a.token_expires_at) if a.token_expires_at else None
            ),
            is_active=a.is_active,
        )


class ManualAccountIn(BaseModel):
    display_name: str = ""
    platform_account_id: str
    access_token: str
    refresh_token: str | None = None
    token_expires_at: str | None = None  # "YYYY-MM-DD" or datetime-local
    action: str = "save"  # "save" | "verify"


# ── Drafting ──────────────────────────────────────────────────────────────────
class DraftRequestIn(BaseModel):
    brief: str
    tone: str = "professional"
    model: str = ""
    account_ids: list[int] = []


class DraftItemOut(BaseModel):
    account_id: int
    platform: str
    display_name: str
    body: str
    limit: int


# ── Posts ─────────────────────────────────────────────────────────────────────
class MediaOut(BaseModel):
    id: int
    url: str
    content_type: str
    kind: str
    filename: str

    @classmethod
    def from_orm_asset(cls, a: MediaAsset) -> "MediaOut":
        return cls(
            id=a.id,
            url=a.public_url or "",
            content_type=a.content_type,
            kind=a.kind,
            filename=a.filename,
        )


class ComposeItemIn(BaseModel):
    account_id: int
    body: str
    media_ids: list[int] = []


class CreatePostsIn(BaseModel):
    action: str = "review"  # "review" | "schedule"
    used_ai: bool = False
    ai_model: str | None = None
    scheduled_time: str | None = None  # datetime-local "YYYY-MM-DDTHH:MM"
    items: list[ComposeItemIn] = []


class ApproveIn(BaseModel):
    body: str
    scheduled_time: str  # datetime-local


class TargetOut(BaseModel):
    id: int
    platform: str
    display_name: str
    status: str
    platform_post_id: str | None
    error_message: str | None

    @classmethod
    def from_orm_target(cls, t: PostTarget) -> "TargetOut":
        return cls(
            id=t.id,
            platform=t.account.platform.value,
            display_name=t.account.display_name,
            status=t.status.value,
            platform_post_id=t.platform_post_id,
            error_message=t.error_message,
        )


class PostOut(BaseModel):
    id: int
    body: str
    status: str
    source: str
    ai_provider: str | None
    ai_model: str | None
    scheduled_time: str | None
    scheduled_time_display: str
    created_at: str | None
    targets: list[TargetOut]
    media: list[MediaOut]

    @classmethod
    def from_orm_post(cls, p: Post, media_assets: list[MediaAsset] = ()) -> "PostOut":
        return cls(
            id=p.id,
            body=p.body,
            status=p.status.value,
            source=p.source.value,
            ai_provider=p.ai_provider.value if p.ai_provider else None,
            ai_model=p.ai_model,
            scheduled_time=_iso(p.scheduled_time),
            scheduled_time_display=utc_to_local_str(p.scheduled_time),
            created_at=_iso(p.created_at),
            targets=[TargetOut.from_orm_target(t) for t in p.targets],
            media=[MediaOut.from_orm_asset(a) for a in media_assets],
        )


class CalendarDayOut(BaseModel):
    day: str
    posts: list[PostOut]


# ── Post → PostOut helpers (batch-load attached media in one query) ───────────
def posts_out(session: Session, posts: list[Post]) -> list[PostOut]:
    ids = {mid for p in posts for mid in (p.media or [])}
    amap: dict[int, MediaAsset] = {}
    if ids:
        amap = {m.id: m for m in session.scalars(select(MediaAsset).where(MediaAsset.id.in_(ids)))}
    out: list[PostOut] = []
    for p in posts:
        assets = [amap[i] for i in (p.media or []) if i in amap]
        out.append(PostOut.from_orm_post(p, assets))
    return out


def post_out(session: Session, post: Post) -> PostOut:
    return posts_out(session, [post])[0]


def platform_meta() -> list[PlatformMetaOut]:
    return [
        PlatformMetaOut(
            value=p.value,
            label=p.value.capitalize(),
            color=PLATFORM_BRAND[p.value],
            char_limit=PLATFORM_CHAR_LIMITS[p],
        )
        for p in Platform
    ]
