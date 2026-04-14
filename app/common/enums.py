from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    SUPERVISOR = "supervisor"


class RequestType(StrEnum):
    BUY = "buy"
    RENT = "rent"


class PropertyType(StrEnum):
    APARTMENT = "apartment"
    HOUSE = "house"
    COMMERCIAL = "commercial"
    LAND = "land"


class ClientStatus(StrEnum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    CLOSED_SUCCESS = "closed_success"
    CLOSED_FAILED = "closed_failed"


class PropertyStatus(StrEnum):
    ACTIVE = "active"
    RESERVED = "reserved"
    SOLD = "sold"
    ARCHIVED = "archived"


class TaskStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELED = "canceled"


class ClientActionType(StrEnum):
    NOTE = "note"
    CALL = "call"
    STATUS_CHANGED = "status_changed"
    TASK_ASSIGNED = "task_assigned"
    PROPERTY_SENT = "property_sent"
    SHOWING_CREATED = "showing_created"


class ClientPropertyRelationStatus(StrEnum):
    SENT = "sent"
    VIEWED = "viewed"
    LIKED = "liked"
    REJECTED = "rejected"


class ShowingResult(StrEnum):
    PLANNED = "planned"
    COMPLETED = "completed"
    CANCELED = "canceled"
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"