from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import ClientPropertyRelationStatus
from app.database.base import Base, CreatedAtMixin, IdMixin

if TYPE_CHECKING:
    from app.database.models.client import Client
    from app.database.models.property import Property


class ClientProperty(Base, IdMixin, CreatedAtMixin):
    __tablename__ = "client_properties"
    __table_args__ = (
        UniqueConstraint("client_id", "property_id", name="uq_client_properties_pair"),
        Index("ix_client_properties_status", "relation_status"),
    )

    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    relation_status: Mapped[ClientPropertyRelationStatus] = mapped_column(
        Enum(ClientPropertyRelationStatus, name="client_property_relation_status", native_enum=False),
        nullable=False,
        default=ClientPropertyRelationStatus.SENT,
        server_default=ClientPropertyRelationStatus.SENT.value,
    )

    client: Mapped[Client] = relationship(back_populates="properties")
    property: Mapped[Property] = relationship(back_populates="clients")