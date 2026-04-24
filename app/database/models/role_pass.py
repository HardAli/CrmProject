from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import UserRole
from app.database.base import Base, CreatedAtMixin, IdMixin


class RolePass(Base, IdMixin, CreatedAtMixin):
    __tablename__ = "role_passes"

    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    target_role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False),
        nullable=False,
    )
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    used_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)