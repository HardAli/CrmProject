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


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _get_columns(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def _get_checks(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {constraint["name"] for constraint in inspector.get_check_constraints(table_name) if constraint.get("name")}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "clients"):
        return

    existing_columns = _get_columns(inspector, "clients")

    if "floor" not in existing_columns:
        op.add_column("clients", sa.Column("floor", sa.SmallInteger(), nullable=True))
    if "building_floors" not in existing_columns:
        op.add_column("clients", sa.Column("building_floors", sa.SmallInteger(), nullable=True))

    wall_material_enum = sa.Enum("BRICK", "PANEL", "MONOLITH", name="wall_material", native_enum=False)
    wall_material_enum.create(bind, checkfirst=True)
    if "wall_material" not in existing_columns:
        op.add_column("clients", sa.Column("wall_material", wall_material_enum, nullable=True))

    if "year_built" not in existing_columns:
        op.add_column("clients", sa.Column("year_built", sa.SmallInteger(), nullable=True))

    inspector = sa.inspect(bind)
    existing_checks = _get_checks(inspector, "clients")
    constraints = (
        (op.f("ck_clients_client_floor_positive"), "floor IS NULL OR floor > 0"),
        (op.f("ck_clients_client_building_floors_positive"), "building_floors IS NULL OR building_floors > 0"),
        (op.f("ck_clients_client_floor_lte_building_floors"), "floor IS NULL OR building_floors IS NULL OR floor <= building_floors"),
        (op.f("ck_clients_client_year_built_reasonable"), "year_built IS NULL OR year_built >= 1800"),
    )
    for name, expression in constraints:
        if name not in existing_checks and name.replace("ck_clients_", "") not in existing_checks:
            op.create_check_constraint(name, "clients", expression)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "clients"):
        return

    existing_checks = _get_checks(inspector, "clients")
    for name in (
        op.f("ck_clients_client_year_built_reasonable"),
        op.f("ck_clients_client_floor_lte_building_floors"),
        op.f("ck_clients_client_building_floors_positive"),
        op.f("ck_clients_client_floor_positive"),
    ):
        if name in existing_checks:
            op.drop_constraint(name, "clients", type_="check")

    existing_columns = _get_columns(inspector, "clients")
    for column_name in ("year_built", "wall_material", "building_floors", "floor"):
        if column_name in existing_columns:
            op.drop_column("clients", column_name)

    sa.Enum("BRICK", "PANEL", "MONOLITH", name="wall_material", native_enum=False).drop(bind, checkfirst=True)
