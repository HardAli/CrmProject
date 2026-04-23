"""Add apartment-specific fields to clients.

Revision ID: 20260423_0005
Revises: 20260421_0004
Create Date: 2026-04-23 10:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260423_0005"
down_revision = "20260421_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("clients", sa.Column("floor", sa.SmallInteger(), nullable=True))
    op.add_column("clients", sa.Column("building_floors", sa.SmallInteger(), nullable=True))
    op.add_column(
        "clients",
        sa.Column(
            "wall_material",
            sa.Enum("BRICK", "PANEL", "MONOLITH", name="wall_material", native_enum=False),
            nullable=True,
        ),
    )
    op.add_column("clients", sa.Column("year_built", sa.SmallInteger(), nullable=True))

    op.create_check_constraint(op.f("ck_clients_client_floor_positive"), "clients", "floor IS NULL OR floor > 0")
    op.create_check_constraint(
        op.f("ck_clients_client_building_floors_positive"),
        "clients",
        "building_floors IS NULL OR building_floors > 0",
    )
    op.create_check_constraint(
        op.f("ck_clients_client_floor_lte_building_floors"),
        "clients",
        "floor IS NULL OR building_floors IS NULL OR floor <= building_floors",
    )
    op.create_check_constraint(
        op.f("ck_clients_client_year_built_reasonable"),
        "clients",
        "year_built IS NULL OR year_built >= 1800",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_clients_client_year_built_reasonable"), "clients", type_="check")
    op.drop_constraint(op.f("ck_clients_client_floor_lte_building_floors"), "clients", type_="check")
    op.drop_constraint(op.f("ck_clients_client_building_floors_positive"), "clients", type_="check")
    op.drop_constraint(op.f("ck_clients_client_floor_positive"), "clients", type_="check")

    op.drop_column("clients", "year_built")
    op.drop_column("clients", "wall_material")
    op.drop_column("clients", "building_floors")
    op.drop_column("clients", "floor")

    sa.Enum("BRICK", "PANEL", "MONOLITH", name="wall_material", native_enum=False).drop(op.get_bind(), checkfirst=True)