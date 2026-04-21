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
    op.create_index(op.f("ix_client_photos_client_created"), "client_photos", ["client_id", "created_at"], unique=False)
    op.create_index(op.f("ix_client_photos_client_id"), "client_photos", ["client_id"], unique=False)
    op.create_index(op.f("ix_client_photos_uploaded_by"), "client_photos", ["uploaded_by"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_client_photos_uploaded_by"), table_name="client_photos")
    op.drop_index(op.f("ix_client_photos_client_id"), table_name="client_photos")
    op.drop_index(op.f("ix_client_photos_client_created"), table_name="client_photos")
    op.drop_table("client_photos")