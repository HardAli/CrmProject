from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import TaskStatus
from app.database.base import Base, IdMixin, TimestampMixin

if TYPE_CHECKING:
    from app.database.models.client import Client
    from app.database.models.user import User


class Task(Base, IdMixin, TimestampMixin):
    __tablename__ = "tasks"
    __table_args__ = (Index("ix_tasks_assigned_status_due", "assigned_to", "status", "due_at"),)

    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_to: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status", native_enum=False),
        nullable=False,
        default=TaskStatus.OPEN,
        server_default=TaskStatus.OPEN.value,
        index=True,
    )

    client: Mapped[Client] = relationship(back_populates="tasks")
    assignee: Mapped[User] = relationship(back_populates="assigned_tasks")