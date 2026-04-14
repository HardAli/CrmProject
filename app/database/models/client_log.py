from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import ClientActionType
from app.database.base import Base, CreatedAtMixin, IdMixin

if TYPE_CHECKING:
    from app.database.models.client import Client
    from app.database.models.user import User


class ClientLog(Base, IdMixin, CreatedAtMixin):
    __tablename__ = "client_logs"
    __table_args__ = (
        Index("ix_client_logs_client_created", "client_id", "created_at"),
        Index("ix_client_logs_action_type", "action_type"),
    )

    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action_type: Mapped[ClientActionType] = mapped_column(
        Enum(ClientActionType, name="client_action_type", native_enum=False),
        nullable=False,
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    client: Mapped[Client] = relationship(back_populates="logs")
    user: Mapped[User | None] = relationship(back_populates="client_logs")