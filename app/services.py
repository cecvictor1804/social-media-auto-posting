"""Post lifecycle helpers used by the dashboard routes.

A single composed item becomes one :class:`Post` (with its platform-tailored
body) plus one :class:`PostTarget` pointing at the chosen account. This keeps
per-platform text and per-platform publish status cleanly separated, while the
PostTarget fan-out model still supports same-body multi-target posts if needed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    AIProvider,
    ContentSource,
    Post,
    PostStatus,
    PostTarget,
    SocialAccount,
    TargetStatus,
    utcnow,
)
from app.security import encrypt_token


@dataclass(slots=True)
class ComposedItem:
    account_id: int
    body: str
    media_ids: list[int] = field(default_factory=list)


def active_accounts(session: Session) -> list[SocialAccount]:
    return list(
        session.scalars(
            select(SocialAccount)
            .where(SocialAccount.is_active.is_(True))
            .order_by(SocialAccount.platform, SocialAccount.display_name)
        )
    )


def create_posts(
    session: Session,
    items: list[ComposedItem],
    *,
    scheduled_time: datetime | None,
    source: ContentSource,
    ai_provider: AIProvider | None,
    ai_model: str | None,
    user_id: int | None,
    approve: bool,
) -> list[Post]:
    """Create one Post+Target per composed item.

    ``approve=True`` with a ``scheduled_time`` schedules immediately; otherwise
    the post stays in ``pending_review`` for the hybrid review step.
    """
    status = (
        PostStatus.scheduled
        if approve and scheduled_time is not None
        else PostStatus.pending_review
    )
    posts: list[Post] = []
    for item in items:
        post = Post(
            body=item.body,
            media=list(item.media_ids),
            status=status,
            scheduled_time=scheduled_time,
            source=source,
            ai_provider=ai_provider,
            ai_model=ai_model,
            created_by=user_id,
        )
        post.targets.append(
            PostTarget(social_account_id=item.account_id, status=TargetStatus.pending)
        )
        session.add(post)
        posts.append(post)
    session.commit()
    return posts


def approve_and_schedule(session: Session, post: Post, scheduled_time: datetime) -> None:
    post.scheduled_time = scheduled_time
    post.status = PostStatus.scheduled
    session.commit()


def list_posts(session: Session, statuses: list[PostStatus] | None = None) -> list[Post]:
    stmt = select(Post).options(
        selectinload(Post.targets).selectinload(PostTarget.account)
    )
    if statuses:
        stmt = stmt.where(Post.status.in_(statuses))
    stmt = stmt.order_by(Post.scheduled_time.is_(None), Post.scheduled_time, Post.created_at.desc())
    return list(session.scalars(stmt))


def get_post(session: Session, post_id: int) -> Post | None:
    return session.scalars(
        select(Post)
        .options(selectinload(Post.targets).selectinload(PostTarget.account))
        .where(Post.id == post_id)
    ).first()


def scheduled_posts_by_day(session: Session) -> list[dict]:
    """Agenda for the Calendar view: posts with a scheduled_time, grouped by the
    local calendar day, ordered soonest-first. Returns
    ``[{"day": date, "posts": [Post, ...]}, ...]``.
    """
    from app.timeutil import utc_to_local_str  # local import avoids cycle

    posts = session.scalars(
        select(Post)
        .options(selectinload(Post.targets).selectinload(PostTarget.account))
        .where(Post.scheduled_time.isnot(None))
        .order_by(Post.scheduled_time)
    ).all()

    groups: dict[str, list[Post]] = {}
    order: list[str] = []
    for post in posts:
        day = utc_to_local_str(post.scheduled_time, fmt="%Y-%m-%d (%a)")
        if day not in groups:
            groups[day] = []
            order.append(day)
        groups[day].append(post)
    return [{"day": day, "posts": groups[day]} for day in order]


# ── Account storage (shared by OAuth callback and manual entry) ─────────────
def upsert_social_account(session: Session, connected) -> SocialAccount:
    """Create or update a SocialAccount from a ConnectedAccount, encrypting tokens.

    Matched on (platform, platform_account_id). Reused by the OAuth callback and
    the manual "add account" form so there is a single encrypted storage path.
    """
    account = session.scalars(
        select(SocialAccount).where(
            SocialAccount.platform == connected.platform,
            SocialAccount.platform_account_id == connected.platform_account_id,
        )
    ).first()
    if account is None:
        account = SocialAccount(
            platform=connected.platform,
            platform_account_id=connected.platform_account_id,
        )
        session.add(account)

    account.display_name = connected.display_name
    account.access_token_enc = encrypt_token(connected.access_token)
    account.refresh_token_enc = (
        encrypt_token(connected.refresh_token) if connected.refresh_token else None
    )
    account.token_expires_at = connected.token_expires_at
    account.is_active = True
    account.updated_at = utcnow()
    session.commit()
    return account
