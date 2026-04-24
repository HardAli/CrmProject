from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from sqlalchemy.inspection import inspect as sa_inspect


def serialize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def serialize_model_instance(instance: Any) -> dict[str, Any]:
    mapper = sa_inspect(instance.__class__)
    return {
        column.key: serialize_value(getattr(instance, column.key))
        for column in mapper.columns
    }