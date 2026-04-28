"""Add kitchen_area to properties.

Revision ID: 20260428_0009
Revises: 20260428_0008
Create Date: 2026-04-28 00:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260428_0009"
down_revision = "20260428_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("properties", sa.Column("kitchen_area", sa.Numeric(10, 2), nullable=True))
    op.create_check_constraint(
        op.f("ck_properties_property_kitchen_area_non_negative"),
        "properties",
        "kitchen_area IS NULL OR kitchen_area >= 0",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_properties_property_kitchen_area_non_negative"), "properties", type_="check")
    op.drop_column("properties", "kitchen_area")
