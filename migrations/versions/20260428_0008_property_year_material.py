"""Add building year and building material to properties.

Revision ID: 20260428_0008
Revises: 20260427_0007
Create Date: 2026-04-28 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260428_0008"
down_revision = "20260427_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("properties", sa.Column("building_year", sa.SmallInteger(), nullable=True))
    op.add_column("properties", sa.Column("building_material", sa.String(length=50), nullable=True))
    op.create_index("ix_properties_building_year", "properties", ["building_year"], unique=False)
    op.create_index("ix_properties_building_material", "properties", ["building_material"], unique=False)
    op.create_check_constraint(
        op.f("ck_properties_property_building_year_valid"),
        "properties",
        "building_year IS NULL OR (building_year >= 1900 AND building_year <= 2100)",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_properties_property_building_year_valid"), "properties", type_="check")
    op.drop_index("ix_properties_building_material", table_name="properties")
    op.drop_index("ix_properties_building_year", table_name="properties")
    op.drop_column("properties", "building_material")
    op.drop_column("properties", "building_year")
