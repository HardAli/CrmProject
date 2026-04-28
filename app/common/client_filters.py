from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.common.enums import ClientStatus, RequestType

ACTIVE_CLIENT_STATUSES: tuple[ClientStatus, ...] = (
    ClientStatus.NEW,
    ClientStatus.IN_PROGRESS,
    ClientStatus.WAITING,
    ClientStatus.SHOWING,
)

DEFAULT_CLIENT_SORT = "newest"


def get_default_client_filters() -> dict[str, Any]:
    return {
        "statuses": [status.value for status in ACTIVE_CLIENT_STATUSES],
        "deal_types": [],
        "rooms": [],
        "budget_min": None,
        "budget_max": None,
        "districts": [],
        "next_contact_mode": None,
        "task_mode": None,
        "sources": [],
        "object_mode": None,
        "photo_mode": None,
        "activity_mode": None,
        "responsible_mode": "me",
        "created_date_mode": None,
        "notes_mode": None,
        "search_query": None,
        "sort": DEFAULT_CLIENT_SORT,
        "page": 1,
        "quick_filter": None,
    }


def reset_client_filters() -> dict[str, Any]:
    return get_default_client_filters()


def update_client_filter(filters: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    updated = deepcopy(filters)
    for key, value in kwargs.items():
        updated[key] = value

    if any(key != "page" for key in kwargs):
        updated["page"] = 1

    return updated


def normalize_filters(raw_filters: dict[str, Any] | None) -> dict[str, Any]:
    base = get_default_client_filters()
    if not raw_filters:
        return base

    base.update(raw_filters)
    base["statuses"] = [value for value in base.get("statuses", []) if value in {status.value for status in ClientStatus}]
    base["deal_types"] = [value for value in base.get("deal_types", []) if value in {rt.value for rt in RequestType}]
    base["rooms"] = [str(value).strip() for value in base.get("rooms", []) if str(value).strip()]
    base["districts"] = [str(value).strip() for value in base.get("districts", []) if str(value).strip()]
    base["sources"] = [str(value).strip() for value in base.get("sources", []) if str(value).strip()]
    base["page"] = max(1, int(base.get("page") or 1))
    base["sort"] = str(base.get("sort") or DEFAULT_CLIENT_SORT)
    return base
