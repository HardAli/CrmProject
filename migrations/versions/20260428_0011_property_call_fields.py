"""Add call tracking fields to properties.

Revision ID: 20260428_0011
Revises: 20260428_0010
Create Date: 2026-04-28 01:30:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260428_0011"
down_revision = "20260428_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("properties", sa.Column("last_call_status", sa.String(length=30), nullable=True))
    op.add_column("properties", sa.Column("last_call_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("properties", sa.Column("next_call_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("properties", sa.Column("call_attempts", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("properties", "call_attempts")
    op.drop_column("properties", "next_call_at")
    op.drop_column("properties", "last_call_at")
    op.drop_column("properties", "last_call_status")
