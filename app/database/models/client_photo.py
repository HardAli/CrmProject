from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, IdMixin

if TYPE_CHECKING:
    from app.database.models.client import Client
    from app.database.models.user import User


class ClientPhoto(Base, IdMixin):
    __tablename__ = "client_photos"
    __table_args__ = (
        Index("ix_client_photos_client_created", "client_id", "created_at"),
    )

    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    telegram_file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    telegram_file_unique_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    client: Mapped[Client] = relationship(back_populates="photos")
    uploaded_by_user: Mapped[User] = relationship(back_populates="uploaded_client_photos")
