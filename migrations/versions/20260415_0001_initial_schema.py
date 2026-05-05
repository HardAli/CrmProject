"""Initial CRM schema.

Revision ID: 20260415_0001
Revises:
Create Date: 2026-04-15 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260415_0001"
down_revision = None
branch_labels = None
depends_on = None


user_role_enum = sa.Enum("admin", "manager", "supervisor", name="user_role", native_enum=False)
request_type_enum = sa.Enum("buy", "sell", "rent", "rent_out", name="request_type", native_enum=False)
property_type_enum = sa.Enum("apartment", "house", "commercial", "land", name="property_type", native_enum=False)
client_status_enum = sa.Enum(
    "new",
    "in_progress",
    "waiting",
    "closed_success",
    "closed_failed",
    name="client_status",
    native_enum=False,
)
property_status_enum = sa.Enum("active", "reserved", "sold", "archived", name="property_status", native_enum=False)
task_status_enum = sa.Enum("open", "in_progress", "done", "canceled", name="task_status", native_enum=False)
client_action_type_enum = sa.Enum(
    "note",
    "call",
    "status_changed",
    "task_assigned",
    "property_sent",
    "showing_created",
    name="client_action_type",
    native_enum=False,
)
relation_status_enum = sa.Enum("sent", "viewed", "liked", "rejected", name="client_property_relation_status", native_enum=False)
showing_result_enum = sa.Enum(
    "planned",
    "completed",
    "canceled",
    "interested",
    "not_interested",
    name="showing_result",
    native_enum=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "users" in inspector.get_table_names():
        return

    op.create_table(
        "users",
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("telegram_id", name=op.f("uq_users_telegram_id")),
    )
    op.create_index(op.f("ix_users_telegram_id"), "users", ["telegram_id"], unique=False)

    op.create_table(
        "clients",
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("request_type", request_type_enum, nullable=False),
        sa.Column("property_type", property_type_enum, nullable=False),
        sa.Column("district", sa.String(length=120), nullable=True),
        sa.Column("rooms", sa.SmallInteger(), nullable=True),
        sa.Column("budget_min", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("budget_max", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("status", client_status_enum, server_default="new", nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("next_contact_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("manager_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("budget_max IS NULL OR budget_max >= 0", name=op.f("ck_clients_budget_max_non_negative")),
        sa.CheckConstraint("budget_min IS NULL OR budget_min >= 0", name=op.f("ck_clients_budget_min_non_negative")),
        sa.CheckConstraint(
            "budget_min IS NULL OR budget_max IS NULL OR budget_min <= budget_max",
            name=op.f("ck_clients_budget_range_valid"),
        ),
        sa.CheckConstraint("rooms IS NULL OR rooms > 0", name=op.f("ck_clients_client_rooms_positive")),
        sa.ForeignKeyConstraint(["manager_id"], ["users.id"], name=op.f("fk_clients_manager_id_users"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clients")),
    )
    op.create_index(op.f("ix_clients_budget_range"), "clients", ["budget_min", "budget_max"], unique=False)
    op.create_index(op.f("ix_clients_district"), "clients", ["district"], unique=False)
    op.create_index(op.f("ix_clients_manager_id"), "clients", ["manager_id"], unique=False)
    op.create_index(op.f("ix_clients_manager_status"), "clients", ["manager_id", "status"], unique=False)
    op.create_index(op.f("ix_clients_next_contact_at"), "clients", ["next_contact_at"], unique=False)
    op.create_index(op.f("ix_clients_phone"), "clients", ["phone"], unique=False)
    op.create_index(op.f("ix_clients_status"), "clients", ["status"], unique=False)

    op.create_table(
        "properties",
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("property_type", property_type_enum, nullable=False),
        sa.Column("district", sa.String(length=120), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("area", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("rooms", sa.SmallInteger(), nullable=True),
        sa.Column("floor", sa.SmallInteger(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("link", sa.String(length=2048), nullable=True),
        sa.Column("status", property_status_enum, server_default="active", nullable=False),
        sa.Column("manager_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("area IS NULL OR area >= 0", name=op.f("ck_properties_property_area_non_negative")),
        sa.CheckConstraint("floor IS NULL OR floor >= 0", name=op.f("ck_properties_property_floor_non_negative")),
        sa.CheckConstraint("price >= 0", name=op.f("ck_properties_property_price_non_negative")),
        sa.CheckConstraint("rooms IS NULL OR rooms > 0", name=op.f("ck_properties_property_rooms_positive")),
        sa.ForeignKeyConstraint(["manager_id"], ["users.id"], name=op.f("fk_properties_manager_id_users"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_properties")),
    )
    op.create_index(op.f("ix_properties_district"), "properties", ["district"], unique=False)
    op.create_index(op.f("ix_properties_filters"), "properties", ["district", "property_type", "status"], unique=False)
    op.create_index(op.f("ix_properties_manager_id"), "properties", ["manager_id"], unique=False)
    op.create_index(op.f("ix_properties_price_rooms"), "properties", ["price", "rooms"], unique=False)
    op.create_index(op.f("ix_properties_property_type"), "properties", ["property_type"], unique=False)
    op.create_index(op.f("ix_properties_status"), "properties", ["status"], unique=False)

    op.create_table(
        "client_logs",
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action_type", client_action_type_enum, nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], name=op.f("fk_client_logs_client_id_clients"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_client_logs_user_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_client_logs")),
    )
    op.create_index(op.f("ix_client_logs_action_type"), "client_logs", ["action_type"], unique=False)
    op.create_index(op.f("ix_client_logs_client_created"), "client_logs", ["client_id", "created_at"], unique=False)
    op.create_index(op.f("ix_client_logs_client_id"), "client_logs", ["client_id"], unique=False)
    op.create_index(op.f("ix_client_logs_user_id"), "client_logs", ["user_id"], unique=False)

    op.create_table(
        "client_properties",
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("relation_status", relation_status_enum, server_default="sent", nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], name=op.f("fk_client_properties_client_id_clients"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"], name=op.f("fk_client_properties_property_id_properties"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_client_properties")),
        sa.UniqueConstraint("client_id", "property_id", name=op.f("uq_client_properties_pair")),
    )
    op.create_index(op.f("ix_client_properties_client_id"), "client_properties", ["client_id"], unique=False)
    op.create_index(op.f("ix_client_properties_property_id"), "client_properties", ["property_id"], unique=False)
    op.create_index(op.f("ix_client_properties_status"), "client_properties", ["relation_status"], unique=False)

    op.create_table(
        "showings",
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("manager_id", sa.Integer(), nullable=False),
        sa.Column("showing_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("result", showing_result_enum, server_default="planned", nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], name=op.f("fk_showings_client_id_clients"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["manager_id"], ["users.id"], name=op.f("fk_showings_manager_id_users"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"], name=op.f("fk_showings_property_id_properties"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_showings")),
    )
    op.create_index(op.f("ix_showings_client_id"), "showings", ["client_id"], unique=False)
    op.create_index(op.f("ix_showings_manager_id"), "showings", ["manager_id"], unique=False)
    op.create_index(op.f("ix_showings_property_id"), "showings", ["property_id"], unique=False)
    op.create_index(op.f("ix_showings_schedule"), "showings", ["manager_id", "showing_at"], unique=False)
    op.create_index(op.f("ix_showings_showing_at"), "showings", ["showing_at"], unique=False)

    op.create_table(
        "tasks",
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("assigned_to", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", task_status_enum, server_default="open", nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"], name=op.f("fk_tasks_assigned_to_users"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], name=op.f("fk_tasks_client_id_clients"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tasks")),
    )
    op.create_index(op.f("ix_tasks_assigned_status_due"), "tasks", ["assigned_to", "status", "due_at"], unique=False)
    op.create_index(op.f("ix_tasks_assigned_to"), "tasks", ["assigned_to"], unique=False)
    op.create_index(op.f("ix_tasks_client_id"), "tasks", ["client_id"], unique=False)
    op.create_index(op.f("ix_tasks_due_at"), "tasks", ["due_at"], unique=False)
    op.create_index(op.f("ix_tasks_status"), "tasks", ["status"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "users" not in inspector.get_table_names():
        return

    op.drop_index(op.f("ix_tasks_status"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_due_at"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_client_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_assigned_to"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_assigned_status_due"), table_name="tasks")
    op.drop_table("tasks")

    op.drop_index(op.f("ix_showings_showing_at"), table_name="showings")
    op.drop_index(op.f("ix_showings_schedule"), table_name="showings")
    op.drop_index(op.f("ix_showings_property_id"), table_name="showings")
    op.drop_index(op.f("ix_showings_manager_id"), table_name="showings")
    op.drop_index(op.f("ix_showings_client_id"), table_name="showings")
    op.drop_table("showings")

    op.drop_index(op.f("ix_client_properties_status"), table_name="client_properties")
    op.drop_index(op.f("ix_client_properties_property_id"), table_name="client_properties")
    op.drop_index(op.f("ix_client_properties_client_id"), table_name="client_properties")
    op.drop_table("client_properties")

    op.drop_index(op.f("ix_client_logs_user_id"), table_name="client_logs")
    op.drop_index(op.f("ix_client_logs_client_id"), table_name="client_logs")
    op.drop_index(op.f("ix_client_logs_client_created"), table_name="client_logs")
    op.drop_index(op.f("ix_client_logs_action_type"), table_name="client_logs")
    op.drop_table("client_logs")

    op.drop_index(op.f("ix_properties_status"), table_name="properties")
    op.drop_index(op.f("ix_properties_property_type"), table_name="properties")
    op.drop_index(op.f("ix_properties_price_rooms"), table_name="properties")
    op.drop_index(op.f("ix_properties_manager_id"), table_name="properties")
    op.drop_index(op.f("ix_properties_filters"), table_name="properties")
    op.drop_index(op.f("ix_properties_district"), table_name="properties")
    op.drop_table("properties")

    op.drop_index(op.f("ix_clients_status"), table_name="clients")
    op.drop_index(op.f("ix_clients_phone"), table_name="clients")
    op.drop_index(op.f("ix_clients_next_contact_at"), table_name="clients")
    op.drop_index(op.f("ix_clients_manager_status"), table_name="clients")
    op.drop_index(op.f("ix_clients_manager_id"), table_name="clients")
    op.drop_index(op.f("ix_clients_district"), table_name="clients")
    op.drop_index(op.f("ix_clients_budget_range"), table_name="clients")
    op.drop_table("clients")

    op.drop_index(op.f("ix_users_telegram_id"), table_name="users")
    op.drop_table("users")