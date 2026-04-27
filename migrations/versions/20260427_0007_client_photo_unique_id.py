"""Add unique id column for client photos deduplication.

Revision ID: 20260427_0007
Revises: 20260424_0006
Create Date: 2026-04-27 10:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260427_0007"
down_revision = "20260424_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("client_photos", sa.Column("telegram_file_unique_id", sa.String(length=255), nullable=True))
    op.create_index(
        op.f("ix_client_photos_telegram_file_unique_id"),
        "client_photos",
        ["telegram_file_unique_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_client_photos_telegram_file_unique_id"), table_name="client_photos")
    op.drop_column("client_photos", "telegram_file_unique_id")
