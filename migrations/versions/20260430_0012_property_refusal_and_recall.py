"""add recall and refusal managers fields to properties

Revision ID: 20260430_0012
Revises: 20260428_0011_property_call_fields
Create Date: 2026-04-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260430_0012"
down_revision = "20260428_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("properties")}

    if "refused_manager_names" not in columns:
        op.add_column("properties", sa.Column("refused_manager_names", sa.Text(), nullable=True))

    if "needs_recall" not in columns:
        op.add_column(
            "properties",
            sa.Column("needs_recall", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )
        op.alter_column("properties", "needs_recall", server_default=None)

    indexes = {idx["name"] for idx in inspector.get_indexes("properties")}
    needs_recall_idx = op.f("ix_properties_needs_recall")
    if needs_recall_idx not in indexes:
        op.create_index(needs_recall_idx, "properties", ["needs_recall"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_properties_needs_recall"), table_name="properties")
    op.drop_column("properties", "needs_recall")
    op.drop_column("properties", "refused_manager_names")
