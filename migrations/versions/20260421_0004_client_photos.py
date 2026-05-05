"""Add client photos table.

Revision ID: 20260421_0004
Revises: 20260421_0003
Create Date: 2026-04-21 00:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260421_0004"
down_revision = "20260421_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "client_photos" not in inspector.get_table_names():
        op.create_table(
            "client_photos",
            sa.Column("client_id", sa.Integer(), nullable=False),
            sa.Column("telegram_file_id", sa.String(length=255), nullable=False),
            sa.Column("uploaded_by", sa.Integer(), nullable=False),
            sa.Column("caption", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_client_photos")),
        )

    inspector = sa.inspect(bind)
    existing_indexes = {index["name"] for index in inspector.get_indexes("client_photos")}
    indexes_to_create = (
        (op.f("ix_client_photos_client_created"), ["client_id", "created_at"]),
        (op.f("ix_client_photos_client_id"), ["client_id"]),
        (op.f("ix_client_photos_uploaded_by"), ["uploaded_by"]),
    )
    for index_name, columns in indexes_to_create:
        if index_name not in existing_indexes and index_name.replace("ix_client_photos_", "") not in existing_indexes:
            op.create_index(index_name, "client_photos", columns, unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "client_photos" not in inspector.get_table_names():
        return

    existing_indexes = {index["name"] for index in inspector.get_indexes("client_photos")}
    for index_name in (
        op.f("ix_client_photos_uploaded_by"),
        op.f("ix_client_photos_client_id"),
        op.f("ix_client_photos_client_created"),
    ):
        if index_name in existing_indexes:
            op.drop_index(index_name, table_name="client_photos")

    op.drop_table("client_photos")
