"""Post lifecycle routes: create, queue, review, approve, delete, calendar."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.ai.base import model_info
from app.api.deps import CurrentUser, DBSession
from app.models import ContentSource
from app.schemas import (
    ApproveIn,
    CalendarDayOut,
    CreatePostsIn,
    PostOut,
    post_out,
    posts_out,
)
from app.services import (
    ComposedItem,
    active_accounts,
    approve_and_schedule,
    create_posts,
    get_post,
    list_posts,
    scheduled_posts_by_day,
)
from app.timeutil import parse_local_input

router = APIRouter(prefix="/api", tags=["posts"])


@router.post("/posts")
def create(payload: CreatePostsIn, user: CurrentUser, session: DBSession):
    active_ids = {a.id for a in active_accounts(session)}
    items = [
        ComposedItem(account_id=i.account_id, body=i.body.strip(), media_ids=i.media_ids)
        for i in payload.items
        if (i.body.strip() or i.media_ids) and i.account_id in active_ids
    ]
    if not items:
        raise HTTPException(status_code=400, detail="No content to post.")

    scheduled_time = parse_local_input(payload.scheduled_time) if payload.scheduled_time else None
    if payload.action == "schedule" and scheduled_time is None:
        raise HTTPException(status_code=400, detail="A schedule time is required to schedule.")

    provider = None
    if payload.used_ai and payload.ai_model:
        provider = model_info(payload.ai_model).provider

    create_posts(
        session,
        items,
        scheduled_time=scheduled_time,
        source=ContentSource.ai if payload.used_ai else ContentSource.manual,
        ai_provider=provider,
        ai_model=payload.ai_model if payload.used_ai else None,
        user_id=user.id,
        approve=(payload.action == "schedule"),
    )
    return {"ok": True}


@router.get("/posts", response_model=list[PostOut])
def queue(user: CurrentUser, session: DBSession):
    return posts_out(session, list_posts(session))


@router.get("/posts/{post_id}", response_model=PostOut)
def review(post_id: int, user: CurrentUser, session: DBSession):
    post = get_post(session, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post_out(session, post)


@router.post("/posts/{post_id}/approve")
def approve(post_id: int, payload: ApproveIn, user: CurrentUser, session: DBSession):
    post = get_post(session, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.body = payload.body.strip()
    approve_and_schedule(session, post, parse_local_input(payload.scheduled_time))
    return {"ok": True}


@router.delete("/posts/{post_id}")
def delete_post(post_id: int, user: CurrentUser, session: DBSession):
    post = get_post(session, post_id)
    if post:
        session.delete(post)
        session.commit()
    return {"ok": True}


@router.get("/calendar", response_model=list[CalendarDayOut])
def calendar(user: CurrentUser, session: DBSession):
    return [
        CalendarDayOut(day=d["day"], posts=posts_out(session, d["posts"]))
        for d in scheduled_posts_by_day(session)
    ]
