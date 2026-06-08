from datetime import timedelta

import app.scheduler.service as svc
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
from app.publishers.base import PublishError, PublishResult
from app.security import encrypt_token


def _make_post(session, *, when_offset_minutes: int) -> Post:
    account = SocialAccount(
        platform=Platform.facebook,
        display_name="Test Page",
        platform_account_id="123",
        access_token_enc=encrypt_token("page-token"),
    )
    session.add(account)
    session.flush()
    post = Post(
        body="hello world",
        media=[],
        status=PostStatus.scheduled,
        scheduled_time=utcnow() + timedelta(minutes=when_offset_minutes),
    )
    post.targets.append(PostTarget(social_account_id=account.id, status=TargetStatus.pending))
    session.add(post)
    session.commit()
    return post


def test_due_post_is_published(session, monkeypatch):
    post = _make_post(session, when_offset_minutes=-1)  # already due

    class FakePublisher:
        async def publish(self, account_id, token, request):
            assert token == "page-token"
            assert request.body == "hello world"
            return PublishResult(platform_post_id="fb_999")

    monkeypatch.setattr(svc, "get_publisher", lambda platform: FakePublisher())

    processed = svc.run_due_posts(session)
    assert processed == 1
    session.refresh(post)
    assert post.status == PostStatus.published
    assert post.targets[0].status == TargetStatus.published
    assert post.targets[0].platform_post_id == "fb_999"


def test_media_ids_resolve_to_media_items(session, monkeypatch):
    asset = MediaAsset(
        filename="pic.jpg",
        content_type="image/jpeg",
        storage_path="k.jpg",
        public_url="https://cdn.example/k.jpg",
    )
    session.add(asset)
    session.flush()
    post = _make_post(session, when_offset_minutes=-1)
    post.media = [asset.id]
    session.commit()

    seen = {}

    class CapturePublisher:
        async def publish(self, account_id, token, request):
            seen["media"] = request.media
            return PublishResult(platform_post_id="fb_1")

    monkeypatch.setattr(svc, "get_publisher", lambda platform: CapturePublisher())
    svc.run_due_posts(session)

    assert len(seen["media"]) == 1
    assert seen["media"][0].url == "https://cdn.example/k.jpg"
    assert seen["media"][0].kind == "image"


def test_not_yet_due_is_skipped(session, monkeypatch):
    _make_post(session, when_offset_minutes=30)  # future
    monkeypatch.setattr(svc, "get_publisher", lambda platform: None)
    assert svc.run_due_posts(session) == 0


def test_retryable_failure_returns_to_scheduled(session, monkeypatch):
    post = _make_post(session, when_offset_minutes=-1)

    class FlakyPublisher:
        async def publish(self, account_id, token, request):
            raise PublishError("503 upstream", retryable=True, status=503)

    monkeypatch.setattr(svc, "get_publisher", lambda platform: FlakyPublisher())

    svc.run_due_posts(session)
    session.refresh(post)
    assert post.status == PostStatus.scheduled  # picked up again next poll
    assert post.targets[0].status == TargetStatus.pending
    assert post.targets[0].attempts == 1


def test_permanent_failure_marks_failed(session, monkeypatch):
    post = _make_post(session, when_offset_minutes=-1)

    class BadPublisher:
        async def publish(self, account_id, token, request):
            raise PublishError("400 invalid token", retryable=False, status=400)

    monkeypatch.setattr(svc, "get_publisher", lambda platform: BadPublisher())

    svc.run_due_posts(session)
    session.refresh(post)
    assert post.status == PostStatus.failed
    assert post.targets[0].status == TargetStatus.failed
    assert "400" in post.targets[0].error_message
