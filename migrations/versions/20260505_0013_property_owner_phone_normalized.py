"""add owner_phone_normalized column to properties

Revision ID: 20260505_0013
Revises: 20260430_0012
Create Date: 2026-05-05 00:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260505_0013"
down_revision = "20260430_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("properties", sa.Column("owner_phone_normalized", sa.String(length=32), nullable=True))
    op.create_index(
        "ix_properties_owner_phone_normalized",
        "properties",
        ["owner_phone_normalized"],
        unique=False,
    )
    op.execute("""
        UPDATE properties
        SET owner_phone_normalized = regexp_replace(coalesce(owner_phone, ''), '\\D', '', 'g')
        WHERE owner_phone IS NOT NULL AND owner_phone <> ''
    """)


def downgrade() -> None:
    op.drop_index("ix_properties_owner_phone_normalized", table_name="properties")
    op.drop_column("properties", "owner_phone_normalized")
