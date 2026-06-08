"""SQLAlchemy ORM models.

All timestamps are stored in UTC. Conversion to a user-facing timezone happens
only in the presentation layer.
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Platform(str, enum.Enum):
    facebook = "facebook"
    linkedin = "linkedin"
    threads = "threads"


class PostStatus(str, enum.Enum):
    draft = "draft"
    pending_review = "pending_review"
    approved = "approved"
    scheduled = "scheduled"
    publishing = "publishing"
    published = "published"
    failed = "failed"


class TargetStatus(str, enum.Enum):
    pending = "pending"
    publishing = "publishing"
    published = "published"
    failed = "failed"


class ContentSource(str, enum.Enum):
    ai = "ai"
    manual = "manual"


class AIProvider(str, enum.Enum):
    anthropic = "anthropic"
    openai = "openai"
    gemini = "gemini"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SocialAccount(Base):
    """A connected platform account (e.g. one Facebook Page, one LinkedIn profile)."""

    __tablename__ = "social_accounts"
    __table_args__ = (
        UniqueConstraint("platform", "platform_account_id", name="uq_account_platform"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    platform: Mapped[Platform] = mapped_column(Enum(Platform), index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    # FB Page ID / LinkedIn member-or-org URN / Threads user ID.
    platform_account_id: Mapped[str] = mapped_column(String(255))

    # Tokens are Fernet-encrypted before storage (see app.security).
    access_token_enc: Mapped[str] = mapped_column(Text)
    refresh_token_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    targets: Mapped[list[PostTarget]] = relationship(back_populates="account")


class Post(Base):
    """A unit of content the user wants published, possibly to several platforms."""

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    body: Mapped[str] = mapped_column(Text)
    # List of MediaAsset ids (kept as JSON for v1 simplicity).
    media: Mapped[list] = mapped_column(JSON, default=list)

    status: Mapped[PostStatus] = mapped_column(
        Enum(PostStatus), default=PostStatus.draft, index=True
    )
    scheduled_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    source: Mapped[ContentSource] = mapped_column(
        Enum(ContentSource), default=ContentSource.manual
    )
    ai_provider: Mapped[AIProvider | None] = mapped_column(Enum(AIProvider), nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(128), nullable=True)

    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    targets: Mapped[list[PostTarget]] = relationship(
        back_populates="post", cascade="all, delete-orphan"
    )


class PostTarget(Base):
    """Fan-out row: one Post published to one SocialAccount, with its own status."""

    __tablename__ = "post_targets"
    __table_args__ = (
        UniqueConstraint("post_id", "social_account_id", name="uq_target_post_account"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    social_account_id: Mapped[int] = mapped_column(
        ForeignKey("social_accounts.id"), index=True
    )

    status: Mapped[TargetStatus] = mapped_column(
        Enum(TargetStatus), default=TargetStatus.pending, index=True
    )
    platform_post_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    post: Mapped[Post] = relationship(back_populates="targets")
    account: Mapped[SocialAccount] = relationship(back_populates="targets")


class MediaAsset(Base):
    """Uploaded image/video metadata (v1: local/static storage)."""

    __tablename__ = "media_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(512))
    content_type: Mapped[str] = mapped_column(String(128))
    storage_path: Mapped[str] = mapped_column(String(1024))
    # Public URL platforms can fetch from (needed by FB /photos, Threads image).
    public_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    @property
    def kind(self) -> str:
        """`image` or `video`, derived from the stored content type."""
        return "image" if (self.content_type or "").startswith("image/") else "video"
