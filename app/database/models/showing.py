from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import ShowingResult
from app.database.base import Base, CreatedAtMixin, IdMixin

if TYPE_CHECKING:
    from app.database.models.client import Client
    from app.database.models.property import Property
    from app.database.models.user import User


class Showing(Base, IdMixin, CreatedAtMixin):
    __tablename__ = "showings"
    __table_args__ = (Index("ix_showings_schedule", "manager_id", "showing_at"),)

    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    manager_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    showing_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    result: Mapped[ShowingResult] = mapped_column(
        Enum(ShowingResult, name="showing_result", native_enum=False),
        nullable=False,
        default=ShowingResult.PLANNED,
        server_default=ShowingResult.PLANNED.value,
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    client: Mapped[Client] = relationship(back_populates="showings")
    property: Mapped[Property] = relationship(back_populates="showings")
    manager: Mapped[User] = relationship(back_populates="showings")