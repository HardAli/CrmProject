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
    op.add_column("properties", sa.Column("owner_phone", sa.String(length=32), nullable=True))
    op.add_column("properties", sa.Column("building_floors", sa.SmallInteger(), nullable=True))

    op.execute("UPDATE properties SET owner_phone = '+70000000000' WHERE owner_phone IS NULL")

    op.alter_column("properties", "owner_phone", existing_type=sa.String(length=32), nullable=False)
    op.create_check_constraint(
        op.f("ck_properties_property_building_floors_positive"),
        "properties",
        "building_floors IS NULL OR building_floors > 0",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_properties_property_building_floors_positive"), "properties", type_="check")
    op.drop_column("properties", "building_floors")
    op.drop_column("properties", "owner_phone")
