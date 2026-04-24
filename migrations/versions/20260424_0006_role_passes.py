"""Add role passes table for one-time role grants.

Revision ID: 20260424_0006
Revises: 20260423_0005
Create Date: 2026-04-24 12:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260424_0006"
down_revision = "20260423_0005"
branch_labels = None
depends_on = None


user_role_enum = sa.Enum("admin", "manager", "supervisor", name="user_role", native_enum=False)


def upgrade() -> None:
    op.create_table(
        "role_passes",
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("target_role", user_role_enum, nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("is_used", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("used_by", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_role_passes_created_by_users"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["used_by"], ["users.id"], name=op.f("fk_role_passes_used_by_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_role_passes")),
        sa.UniqueConstraint("code", name=op.f("uq_role_passes_code")),
    )
    op.create_index(op.f("ix_role_passes_code"), "role_passes", ["code"], unique=False)
    op.create_index(op.f("ix_role_passes_created_by"), "role_passes", ["created_by"], unique=False)
    op.create_index(op.f("ix_role_passes_expires_at"), "role_passes", ["expires_at"], unique=False)
    op.create_index(op.f("ix_role_passes_used_by"), "role_passes", ["used_by"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_role_passes_used_by"), table_name="role_passes")
    op.drop_index(op.f("ix_role_passes_expires_at"), table_name="role_passes")
    op.drop_index(op.f("ix_role_passes_created_by"), table_name="role_passes")
    op.drop_index(op.f("ix_role_passes_code"), table_name="role_passes")
    op.drop_table("role_passes")