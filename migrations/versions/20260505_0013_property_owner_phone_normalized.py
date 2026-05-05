"""add owner_phone_normalized column to properties

Revision ID: 20260505_0013
Revises: 20260430_0012
Create Date: 2026-05-05 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "20260505_0013"
down_revision = "20260430_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("properties")}
    indexes = {index["name"] for index in inspector.get_indexes("properties")}

    if "owner_phone_normalized" not in columns:
        op.add_column("properties", sa.Column("owner_phone_normalized", sa.String(length=20), nullable=True))

    if "refused_manager_names" not in columns:
        op.add_column("properties", sa.Column("refused_manager_names", sa.Text(), nullable=True))

    if "needs_recall" not in columns:
        op.add_column(
            "properties",
            sa.Column("needs_recall", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )
        op.alter_column("properties", "needs_recall", server_default=None)

    if "ix_properties_owner_phone_normalized" not in indexes:
        op.create_index("ix_properties_owner_phone_normalized", "properties", ["owner_phone_normalized"], unique=False)

    if "ix_properties_needs_recall" not in indexes:
        op.create_index("ix_properties_needs_recall", "properties", ["needs_recall"], unique=False)

    op.execute(
        """
        UPDATE properties
        SET owner_phone_normalized = NULLIF(regexp_replace(coalesce(owner_phone, ''), '\\D', '', 'g'), '')
        WHERE owner_phone_normalized IS NULL
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("properties")}
    indexes = {index["name"] for index in inspector.get_indexes("properties")}

    if "ix_properties_owner_phone_normalized" in indexes:
        op.drop_index("ix_properties_owner_phone_normalized", table_name="properties")

    if "owner_phone_normalized" in columns:
        op.drop_column("properties", "owner_phone_normalized")
