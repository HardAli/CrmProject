from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import PropertyStatus, PropertyType
from app.database.base import Base, IdMixin, TimestampMixin

if TYPE_CHECKING:
    from app.database.models.client import Client
    from app.database.models.client_property import ClientProperty
    from app.database.models.showing import Showing
    from app.database.models.user import User


class Property(Base, IdMixin, TimestampMixin):
    __tablename__ = "properties"
    __table_args__ = (
        CheckConstraint("price >= 0", name="property_price_non_negative"),
        CheckConstraint("area IS NULL OR area >= 0", name="property_area_non_negative"),
        CheckConstraint("floor IS NULL OR floor >= 0", name="property_floor_non_negative"),
        CheckConstraint(
            "building_floors IS NULL OR building_floors > 0",
            name="property_building_floors_positive",
        ),
        Index("ix_properties_filters", "district", "property_type", "status"),
        Index("ix_properties_price_rooms", "price", "rooms"),
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    property_type: Mapped[PropertyType] = mapped_column(
        Enum(PropertyType, name="property_type", native_enum=False),
        nullable=False,
        index=True,
    )
    district: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    owner_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    area: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    rooms: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    floor: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    building_floors: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    link: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    status: Mapped[PropertyStatus] = mapped_column(
        Enum(PropertyStatus, name="property_status", native_enum=False),
        nullable=False,
        default=PropertyStatus.ACTIVE,
        server_default=PropertyStatus.ACTIVE.value,
        index=True,
    )

    manager_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    manager: Mapped[User] = relationship(back_populates="managed_properties")
    clients: Mapped[list[ClientProperty]] = relationship(back_populates="property", cascade="all, delete-orphan")
    related_clients: Mapped[list[Client]] = relationship(
        secondary="client_properties",
        primaryjoin="Property.id == ClientProperty.property_id",
        secondaryjoin="Client.id == ClientProperty.client_id",
        viewonly=True,
    )
    showings: Mapped[list[Showing]] = relationship(back_populates="property", cascade="all, delete-orphan")
