"""add recall and refusal managers fields to properties

Revision ID: 20260430_0012
Revises: 20260428_0011_property_call_fields
Create Date: 2026-04-30
"""

from alembic import op
import sqlalchemy as sa


revision = "20260430_0012"
down_revision = "20260428_0011_property_call_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("properties", sa.Column("refused_manager_names", sa.Text(), nullable=True))
    op.add_column("properties", sa.Column("needs_recall", sa.Boolean(), nullable=False, server_default=sa.text("0")))
    op.create_index("ix_properties_needs_recall", "properties", ["needs_recall"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_properties_needs_recall", table_name="properties")
    op.drop_column("properties", "needs_recall")
    op.drop_column("properties", "refused_manager_names")
