from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import ClientStatus, PropertyType, RequestType
from app.database.base import Base, IdMixin, TimestampMixin

if TYPE_CHECKING:
    from app.database.models.client_log import ClientLog
    from app.database.models.client_property import ClientProperty
    from app.database.models.property import Property
    from app.database.models.showing import Showing
    from app.database.models.task import Task
    from app.database.models.user import User


class Client(Base, IdMixin, TimestampMixin):
    __tablename__ = "clients"
    __table_args__ = (
        CheckConstraint("budget IS NULL OR budget >= 0", name="budget_non_negative"),
        Index("ix_clients_manager_status", "manager_id", "status"),
        Index("ix_clients_next_contact_at", "next_contact_at"),
        Index("ix_clients_district", "district"),
        Index("ix_clients_budget", "budget"),
    )

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    request_type: Mapped[RequestType] = mapped_column(
        Enum(RequestType, name="request_type", native_enum=False),
        nullable=False,
    )
    property_type: Mapped[PropertyType] = mapped_column(
        Enum(PropertyType, name="property_type", native_enum=False),
        nullable=False,
    )
    district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    rooms: Mapped[str | None] = mapped_column(String(32), nullable=True)
    budget: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    status: Mapped[ClientStatus] = mapped_column(
        Enum(ClientStatus, name="client_status", native_enum=False),
        nullable=False,
        default=ClientStatus.NEW,
        server_default=ClientStatus.NEW.value,
        index=True,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_contact_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    manager_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    manager: Mapped[User] = relationship(back_populates="managed_clients")
    tasks: Mapped[list[Task]] = relationship(back_populates="client", cascade="all, delete-orphan")
    logs: Mapped[list[ClientLog]] = relationship(back_populates="client", cascade="all, delete-orphan")
    properties: Mapped[list[ClientProperty]] = relationship(back_populates="client", cascade="all, delete-orphan")
    related_properties: Mapped[list[Property]] = relationship(
        secondary="client_properties",
        primaryjoin="Client.id == ClientProperty.client_id",
        secondaryjoin="Property.id == ClientProperty.property_id",
        viewonly=True,
    )
    showings: Mapped[list[Showing]] = relationship(back_populates="client", cascade="all, delete-orphan")