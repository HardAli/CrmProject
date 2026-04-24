from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from sqlalchemy.inspection import inspect as sa_inspect
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import DateTime, Numeric


@dataclass(slots=True)
class ImportMapResult:
    data: dict[str, Any]
    missing_required_fields: list[str]
    ignored_fields: list[str]
    conversion_errors: list[str]


def map_import_record_to_model_fields(record: dict[str, Any], model: type[Any]) -> ImportMapResult:
    mapper = sa_inspect(model)
    columns: dict[str, Column[Any]] = {column.key: column for column in mapper.columns}

    converted: dict[str, Any] = {}
    missing_required: list[str] = []
    ignored_fields: list[str] = []
    conversion_errors: list[str] = []

    for key, value in record.items():
        column = columns.get(key)
        if column is None:
            ignored_fields.append(key)
            continue

        try:
            converted[key] = _convert_value_for_column(value, column)
        except (ValueError, TypeError) as exc:
            conversion_errors.append(f"{key}: {exc}")

    for key, column in columns.items():
        if key in converted:
            continue
        if column.nullable:
            continue
        if column.default is not None or column.server_default is not None:
            continue
        if column.autoincrement is True:
            continue
        missing_required.append(key)

    return ImportMapResult(
        data=converted,
        missing_required_fields=missing_required,
        ignored_fields=ignored_fields,
        conversion_errors=conversion_errors,
    )


def _convert_value_for_column(value: Any, column: Column[Any]) -> Any:
    if value is None:
        return None

    enum_cls = getattr(column.type, "enum_class", None)
    if enum_cls is not None:
        if isinstance(value, enum_cls):
            return value
        if issubclass(enum_cls, Enum):
            return enum_cls(value)

    if isinstance(column.type, Numeric) and not isinstance(value, Decimal):
        return Decimal(str(value))

    if isinstance(column.type, DateTime) and isinstance(value, str):
        return datetime.fromisoformat(value)

    return value