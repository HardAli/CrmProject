from __future__ import annotations


def truncate_text(text: str | None, max_length: int) -> str:
    if max_length <= 0:
        return ""
    value = (text or "").strip()
    if len(value) <= max_length:
        return value
    if max_length <= 1:
        return "…"
    return f"{value[: max_length - 1].rstrip()}…"


def split_message(text: str | None, max_length: int) -> list[str]:
    value = (text or "").strip()
    if not value:
        return [""]
    if max_length <= 0:
        return [value]

    chunks: list[str] = []
    current = ""
    for line in value.splitlines(keepends=True):
        if len(line) > max_length:
            if current:
                chunks.append(current.rstrip())
                current = ""
            for i in range(0, len(line), max_length):
                chunks.append(line[i : i + max_length].rstrip())
            continue
        if len(current) + len(line) <= max_length:
            current += line
            continue
        if current:
            chunks.append(current.rstrip())
        current = line

    if current:
        chunks.append(current.rstrip())
    return chunks or [""]
