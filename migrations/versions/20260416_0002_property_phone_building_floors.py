"""Add owner phone and building floors to properties.

Revision ID: 20260416_0002
Revises: 20260415_0001
Create Date: 2026-04-16 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260416_0002"
down_revision = "20260415_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("properties")}

    if "owner_phone" not in existing_columns:
        op.add_column("properties", sa.Column("owner_phone", sa.String(length=32), nullable=True))

    if "building_floors" not in existing_columns:
        op.add_column("properties", sa.Column("building_floors", sa.SmallInteger(), nullable=True))

    op.execute("UPDATE properties SET owner_phone = '+70000000000' WHERE owner_phone IS NULL")

    op.alter_column("properties", "owner_phone", existing_type=sa.String(length=32), nullable=False)
    existing_checks = {check["name"] for check in inspector.get_check_constraints("properties")}
    constraint_name = op.f("ck_properties_property_building_floors_positive")
    if constraint_name not in existing_checks:
        op.create_check_constraint(
            constraint_name,
            "properties",
            "building_floors IS NULL OR building_floors > 0",
        )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_properties_property_building_floors_positive"), "properties", type_="check")
    op.drop_column("properties", "building_floors")
    op.drop_column("properties", "owner_phone")
