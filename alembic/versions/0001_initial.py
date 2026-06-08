"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-08
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

platform = sa.Enum("facebook", "linkedin", "threads", name="platform")
post_status = sa.Enum(
    "draft", "pending_review", "approved", "scheduled", "publishing", "published", "failed",
    name="poststatus",
)
target_status = sa.Enum("pending", "publishing", "published", "failed", name="targetstatus")
content_source = sa.Enum("ai", "manual", name="contentsource")
ai_provider = sa.Enum("anthropic", "openai", "gemini", name="aiprovider")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "social_accounts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("platform", platform, nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("platform_account_id", sa.String(255), nullable=False),
        sa.Column("access_token_enc", sa.Text, nullable=False),
        sa.Column("refresh_token_enc", sa.Text, nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("platform", "platform_account_id", name="uq_account_platform"),
    )
    op.create_index("ix_social_accounts_platform", "social_accounts", ["platform"])

    op.create_table(
        "posts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("media", sa.JSON, nullable=True),
        sa.Column("status", post_status, nullable=False),
        sa.Column("scheduled_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", content_source, nullable=False),
        sa.Column("ai_provider", ai_provider, nullable=True),
        sa.Column("ai_model", sa.String(128), nullable=True),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_posts_status", "posts", ["status"])
    op.create_index("ix_posts_scheduled_time", "posts", ["scheduled_time"])

    op.create_table(
        "post_targets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "post_id",
            sa.Integer,
            sa.ForeignKey("posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "social_account_id",
            sa.Integer,
            sa.ForeignKey("social_accounts.id"),
            nullable=False,
        ),
        sa.Column("status", target_status, nullable=False),
        sa.Column("platform_post_id", sa.String(255), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("post_id", "social_account_id", name="uq_target_post_account"),
    )
    op.create_index("ix_post_targets_post_id", "post_targets", ["post_id"])
    op.create_index("ix_post_targets_social_account_id", "post_targets", ["social_account_id"])
    op.create_index("ix_post_targets_status", "post_targets", ["status"])

    op.create_table(
        "media_assets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("content_type", sa.String(128), nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("public_url", sa.String(1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("media_assets")
    op.drop_table("post_targets")
    op.drop_table("posts")
    op.drop_table("social_accounts")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    for enum_type in (target_status, post_status, content_source, ai_provider, platform):
        enum_type.drop(op.get_bind(), checkfirst=True)
