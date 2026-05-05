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
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "client_photos" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("client_photos")}
    if "telegram_file_unique_id" not in columns:
        op.add_column("client_photos", sa.Column("telegram_file_unique_id", sa.String(length=255), nullable=True))

    indexes = {index["name"] for index in inspector.get_indexes("client_photos")}
    index_name = op.f("ix_client_photos_telegram_file_unique_id")
    if index_name not in indexes:
        op.create_index(index_name, "client_photos", ["telegram_file_unique_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "client_photos" not in inspector.get_table_names():
        return

    indexes = {index["name"] for index in inspector.get_indexes("client_photos")}
    index_name = op.f("ix_client_photos_telegram_file_unique_id")
    if index_name in indexes:
        op.drop_index(index_name, table_name="client_photos")

    columns = {column["name"] for column in inspector.get_columns("client_photos")}
    if "telegram_file_unique_id" in columns:
        op.drop_column("client_photos", "telegram_file_unique_id")
