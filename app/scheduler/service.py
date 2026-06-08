"""Core publishing logic shared by the scheduler job (and manual "publish now").

Kept free of APScheduler so it can be unit-tested directly with a fake clock.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    MediaAsset,
    Platform,
    Post,
    PostStatus,
    PostTarget,
    SocialAccount,
    TargetStatus,
    utcnow,
)
from app.oauth import get_oauth_provider
from app.publishers import MediaItem, PublishRequest, PublishError, get_publisher
from app.security import decrypt_token, encrypt_token

log = logging.getLogger("smap.scheduler")

# Refresh tokens that expire within this window before using them.
TOKEN_REFRESH_LEEWAY = timedelta(days=2)


def _run(coro):
    """Run an async coroutine from sync scheduler code."""
    return asyncio.run(coro)


def claim_due_posts(session: Session, now: datetime | None = None) -> list[Post]:
    """Atomically claim scheduled posts whose time has arrived.

    Uses ``FOR UPDATE SKIP LOCKED`` on Postgres so concurrent workers never grab
    the same post; on SQLite (single worker, dev) the lock clause is omitted.
    """
    now = now or utcnow()
    stmt = (
        select(Post)
        .where(Post.status == PostStatus.scheduled, Post.scheduled_time <= now)
        .order_by(Post.scheduled_time)
        .limit(50)
    )
    if session.bind.dialect.name == "postgresql":
        stmt = stmt.with_for_update(skip_locked=True)

    posts = list(session.scalars(stmt))
    for post in posts:
        post.status = PostStatus.publishing
    session.commit()
    return posts


def refresh_account_if_needed(session: Session, account: SocialAccount) -> str:
    """Return a valid access token, refreshing + persisting it if near expiry."""
    token = decrypt_token(account.access_token_enc)
    expires = account.token_expires_at
    needs_refresh = expires is not None and expires <= utcnow() + TOKEN_REFRESH_LEEWAY
    if not needs_refresh:
        return token or ""

    provider = get_oauth_provider(account.platform)
    refreshed = _run(provider.refresh(account))
    if refreshed is None:
        return token or ""

    account.access_token_enc = encrypt_token(refreshed.access_token)
    if refreshed.refresh_token is not None:
        account.refresh_token_enc = encrypt_token(refreshed.refresh_token)
    account.token_expires_at = refreshed.token_expires_at
    account.updated_at = utcnow()
    session.commit()
    log.info("Refreshed token for %s account %s", account.platform.value, account.id)
    return refreshed.access_token


def resolve_media(session: Session, media_ids: list) -> list[MediaItem]:
    """Turn a post's stored MediaAsset ids into publisher-ready MediaItems."""
    if not media_ids:
        return []
    rows = {
        m.id: m
        for m in session.scalars(select(MediaAsset).where(MediaAsset.id.in_(media_ids)))
    }
    items: list[MediaItem] = []
    for mid in media_ids:  # preserve the user's ordering
        a = rows.get(mid)
        if a and a.public_url:
            items.append(MediaItem(url=a.public_url, content_type=a.content_type, kind=a.kind))
    return items


def publish_target(session: Session, target: PostTarget, body: str, media: list[MediaItem]) -> None:
    """Publish a single target, updating its status/error/attempts in place."""
    account = target.account
    target.attempts += 1
    target.last_attempt_at = utcnow()
    target.status = TargetStatus.publishing
    session.commit()

    try:
        token = refresh_account_if_needed(session, account)
        publisher = get_publisher(account.platform)
        result = _run(
            publisher.publish(
                account.platform_account_id,
                token,
                PublishRequest(body=body, media=media),
            )
        )
        target.status = TargetStatus.published
        target.platform_post_id = result.platform_post_id
        target.error_message = None
    except PublishError as exc:
        permanently_failed = (
            not exc.retryable or target.attempts >= settings.max_publish_attempts
        )
        target.error_message = str(exc)
        target.status = TargetStatus.failed if permanently_failed else TargetStatus.pending
        log.warning(
            "Publish failed (target=%s attempt=%s retryable=%s): %s",
            target.id, target.attempts, exc.retryable, exc,
        )
    except Exception as exc:  # unexpected — treat as retryable until cap
        target.error_message = f"Unexpected error: {exc}"
        target.status = (
            TargetStatus.failed
            if target.attempts >= settings.max_publish_attempts
            else TargetStatus.pending
        )
        log.exception("Unexpected publish error for target %s", target.id)
    finally:
        session.commit()


def finalize_post(session: Session, post: Post) -> None:
    """Set the post's status from its targets' outcomes."""
    statuses = {t.status for t in post.targets}
    if statuses <= {TargetStatus.published}:
        post.status = PostStatus.published
    elif TargetStatus.pending in statuses or TargetStatus.publishing in statuses:
        # Still has work to do (a retryable target) — return to scheduled so the
        # next poll picks it up again.
        post.status = PostStatus.scheduled
    else:
        post.status = PostStatus.failed
    session.commit()


def publish_post(session: Session, post: Post) -> None:
    media = resolve_media(session, list(post.media or []))
    for target in post.targets:
        if target.status in {TargetStatus.published}:
            continue
        publish_target(session, target, post.body, media)
    finalize_post(session, post)


def run_due_posts(session: Session, now: datetime | None = None) -> int:
    """Claim and publish all due posts. Returns the number processed."""
    posts = claim_due_posts(session, now=now)
    for post in posts:
        publish_post(session, post)
    return len(posts)


def refresh_expiring_tokens(session: Session) -> int:
    """Proactively refresh tokens nearing expiry (daily job). Returns count refreshed."""
    soon = utcnow() + timedelta(days=5)
    accounts = session.scalars(
        select(SocialAccount).where(
            SocialAccount.is_active.is_(True),
            SocialAccount.token_expires_at.isnot(None),
            SocialAccount.token_expires_at <= soon,
        )
    ).all()
    refreshed = 0
    for account in accounts:
        before = account.access_token_enc
        refresh_account_if_needed(session, account)
        if account.access_token_enc != before:
            refreshed += 1
    return refreshed
