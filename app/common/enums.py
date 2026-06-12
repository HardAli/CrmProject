from __future__ import annotations

import enum

StrEnum = getattr(enum, "StrEnum", None)

if StrEnum is None:
    class StrEnum(str, enum.Enum):
        """Backward-compatible StrEnum for Python < 3.11."""


class UserRole(StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    SUPERVISOR = "supervisor"


class RequestType(StrEnum):
    BUY = "buy"
    SELL = "sell"
    RENT = "rent"
    RENT_OUT = "rent_out"


class PropertyType(StrEnum):
    APARTMENT = "apartment"
    HOUSE = "house"
    COMMERCIAL = "commercial"
    LAND = "land"


class WallMaterial(StrEnum):
    BRICK = "brick"
    PANEL = "panel"
    MONOLITH = "monolith"


class ClientStatus(StrEnum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    SHOWING = "showing"
    CLOSED_SUCCESS = "closed_success"
    CLOSED_FAILED = "closed_failed"


class BuyerRequestStatus(StrEnum):
    NEW = "new"
    IN_WORK = "in_work"
    SELECTING_PROPERTIES = "selecting_properties"
    VIEWING_SCHEDULED = "viewing_scheduled"
    VIEWED = "viewed"
    THINKING = "thinking"
    READY_FOR_DEPOSIT = "ready_for_deposit"
    BOUGHT = "bought"
    POSTPONED = "postponed"
    NOT_ACTUAL = "not_actual"
    NO_ANSWER = "no_answer"
    REFUSED_TO_WORK = "refused_to_work"


class PropertyStatus(StrEnum):
    ACTIVE = "active"
    RESERVED = "reserved"
    AGREED = "agreed"
    NOT_REACHED = "not_reached"
    REFUSED_TO_WORK = "refused_to_work"
    SOLD = "sold"
    ARCHIVED = "archived"
    EXTERNAL_AGENCY = "external_agency"


class TaskStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELED = "canceled"


class ClientActionType(StrEnum):
    CLIENT_CREATED = "client_created"
    BUYER_REQUEST_CREATED = "buyer_request_created"
    BUYER_REQUEST_STATUS_CHANGED = "buyer_request_status_changed"
    BUYER_PROPERTY_OFFERED = "buyer_property_offered"
    STATUS_CHANGED = "status_changed"
    NOTE_ADDED = "note_added"
    CARD_VIEWED = "card_viewed"
    TASK_CREATED = "task_created"
    NEXT_CONTACT_CHANGED = "next_contact_changed"
    PROPERTY_LINKED = "property_linked"
    PROPERTY_RELATION_STATUS_CHANGED = "property_relation_status_changed"
    AUTO_LINKED_BY_PHONE = "auto_linked_by_phone"


class ClientPropertyRelationStatus(StrEnum):
    SENT = "sent"
    INTERESTED = "interested"
    SHOWN = "shown"
    REJECTED = "rejected"
    IN_NEGOTIATION = "in_negotiation"
    DEAL = "deal"


class PropertySelectionFeedbackAction(StrEnum):
    VIEWED = "viewed"
    INTERESTED = "interested"
    REJECTED = "rejected"
    FAVORITE = "favorite"
    WANTS_CALL = "wants_call"
    WANTS_VIEWING = "wants_viewing"
    COMMENT = "comment"


class PropertySelectionStatus(StrEnum):
    DRAFT = "draft"
    SENT = "sent"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ShowingResult(StrEnum):
    PLANNED = "planned"
    COMPLETED = "completed"
    CANCELED = "canceled"
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
