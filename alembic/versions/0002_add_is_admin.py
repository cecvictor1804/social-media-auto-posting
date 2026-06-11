"""add is_admin to users

Revision ID: 0002_add_is_admin
Revises: 0001_initial
Create Date: 2026-06-12
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_add_is_admin"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_admin",
                sa.Boolean,
                nullable=False,
                server_default=sa.false(),
            )
        )
    # Grant admin to every user that existed before multi-user support
    # (covers the single bootstrap admin and avoids lockout).
    op.execute("UPDATE users SET is_admin = TRUE")


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("is_admin")
