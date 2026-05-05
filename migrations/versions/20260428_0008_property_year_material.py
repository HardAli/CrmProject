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
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "properties" not in inspector.get_table_names():
        return

    columns = {c["name"] for c in inspector.get_columns("properties")}
    if "building_year" not in columns:
        op.add_column("properties", sa.Column("building_year", sa.SmallInteger(), nullable=True))
    if "building_material" not in columns:
        op.add_column("properties", sa.Column("building_material", sa.String(length=50), nullable=True))

    inspector = sa.inspect(bind)
    indexes = {idx["name"] for idx in inspector.get_indexes("properties")}
    if "ix_properties_building_year" not in indexes:
        op.create_index("ix_properties_building_year", "properties", ["building_year"], unique=False)
    if "ix_properties_building_material" not in indexes:
        op.create_index("ix_properties_building_material", "properties", ["building_material"], unique=False)

    checks = {c["name"] for c in inspector.get_check_constraints("properties") if c.get("name")}
    check_name = op.f("ck_properties_property_building_year_valid")
    if check_name not in checks and "ck_properties_property_building_year_valid" not in checks:
        op.create_check_constraint(
            check_name,
            "properties",
            "building_year IS NULL OR (building_year >= 1900 AND building_year <= 2100)",
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "properties" not in inspector.get_table_names():
        return

    checks = {c["name"] for c in inspector.get_check_constraints("properties") if c.get("name")}
    check_name = op.f("ck_properties_property_building_year_valid")
    if check_name in checks:
        op.drop_constraint(check_name, "properties", type_="check")

    indexes = {idx["name"] for idx in inspector.get_indexes("properties")}
    if "ix_properties_building_material" in indexes:
        op.drop_index("ix_properties_building_material", table_name="properties")
    if "ix_properties_building_year" in indexes:
        op.drop_index("ix_properties_building_year", table_name="properties")

    columns = {c["name"] for c in inspector.get_columns("properties")}
    if "building_material" in columns:
        op.drop_column("properties", "building_material")
    if "building_year" in columns:
        op.drop_column("properties", "building_year")
