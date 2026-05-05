"""Replace client budget range with single budget and text rooms.

Revision ID: 20260421_0003
Revises: 20260416_0002
Create Date: 2026-04-21 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260421_0003"
down_revision = "20260416_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_indexes = {index["name"] for index in inspector.get_indexes("clients")}
    for index_name in (op.f("ix_clients_budget_range"), "ix_clients_budget_range"):
        if index_name in existing_indexes:
            op.drop_index(index_name, table_name="clients")
            break

    existing_checks = {constraint["name"] for constraint in inspector.get_check_constraints("clients")}
    for check_name in (
        op.f("ck_clients_budget_range_valid"),
        op.f("ck_clients_budget_max_non_negative"),
        op.f("ck_clients_budget_min_non_negative"),
        op.f("ck_clients_client_rooms_positive"),
        "ck_clients_budget_range_valid",
        "ck_clients_budget_max_non_negative",
        "ck_clients_budget_min_non_negative",
        "ck_clients_client_rooms_positive",
    ):
        if check_name in existing_checks:
            op.drop_constraint(check_name, "clients", type_="check")

    op.add_column("clients", sa.Column("budget", sa.Numeric(precision=12, scale=2), nullable=True))
    op.execute(
        """
        UPDATE clients
        SET budget = COALESCE(budget_max, budget_min)
        WHERE budget IS NULL
        """
    )

    op.alter_column("clients", "rooms", existing_type=sa.SmallInteger(), type_=sa.String(length=32), existing_nullable=True)
    op.create_check_constraint(op.f("ck_clients_budget_non_negative"), "clients", "budget IS NULL OR budget >= 0")
    op.create_index(op.f("ix_clients_budget"), "clients", ["budget"], unique=False)

    op.drop_column("clients", "budget_min")
    op.drop_column("clients", "budget_max")


def downgrade() -> None:
    op.add_column("clients", sa.Column("budget_max", sa.Numeric(precision=12, scale=2), nullable=True))
    op.add_column("clients", sa.Column("budget_min", sa.Numeric(precision=12, scale=2), nullable=True))

    op.execute(
        """
        UPDATE clients
        SET budget_min = budget,
            budget_max = budget
        """
    )

    op.drop_index(op.f("ix_clients_budget"), table_name="clients")
    op.drop_constraint(op.f("ck_clients_budget_non_negative"), "clients", type_="check")
    op.alter_column("clients", "rooms", existing_type=sa.String(length=32), type_=sa.SmallInteger(), existing_nullable=True)
    op.create_check_constraint(op.f("ck_clients_client_rooms_positive"), "clients", "rooms IS NULL OR rooms > 0")
    op.create_check_constraint(op.f("ck_clients_budget_min_non_negative"), "clients", "budget_min IS NULL OR budget_min >= 0")
    op.create_check_constraint(op.f("ck_clients_budget_max_non_negative"), "clients", "budget_max IS NULL OR budget_max >= 0")
    op.create_check_constraint(
        op.f("ck_clients_budget_range_valid"),
        "clients",
        "budget_min IS NULL OR budget_max IS NULL OR budget_min <= budget_max",
    )
    op.create_index(op.f("ix_clients_budget_range"), "clients", ["budget_min", "budget_max"], unique=False)

    op.drop_column("clients", "budget")