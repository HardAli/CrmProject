"""Create property_call_logs table.

Revision ID: 20260428_0010
Revises: 20260428_0009
Create Date: 2026-04-28 01:20:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260428_0010"
down_revision = "20260428_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "property_call_logs",
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("manager_id", sa.Integer(), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("result", sa.String(length=30), nullable=False),
        sa.Column("reason", sa.String(length=50), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("next_call_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(["manager_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_property_call_logs_manager_id"), "property_call_logs", ["manager_id"], unique=False)
    op.create_index(op.f("ix_property_call_logs_property_id"), "property_call_logs", ["property_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_property_call_logs_property_id"), table_name="property_call_logs")
    op.drop_index(op.f("ix_property_call_logs_manager_id"), table_name="property_call_logs")
    op.drop_table("property_call_logs")
