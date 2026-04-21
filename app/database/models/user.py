from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, Enum, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import UserRole
from app.database.base import Base, CreatedAtMixin, IdMixin

if TYPE_CHECKING:
    from app.database.models.client_photo import ClientPhoto
    from app.database.models.client import Client
    from app.database.models.client_log import ClientLog
    from app.database.models.property import Property
    from app.database.models.showing import Showing
    from app.database.models.task import Task


class User(Base, IdMixin, CreatedAtMixin):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)

    managed_clients: Mapped[list[Client]] = relationship(back_populates="manager")
    managed_properties: Mapped[list[Property]] = relationship(back_populates="manager")
    assigned_tasks: Mapped[list[Task]] = relationship(back_populates="assignee")
    client_logs: Mapped[list[ClientLog]] = relationship(back_populates="user")
    uploaded_client_photos: Mapped[list[ClientPhoto]] = relationship(back_populates="uploaded_by_user")
    showings: Mapped[list[Showing]] = relationship(back_populates="manager")