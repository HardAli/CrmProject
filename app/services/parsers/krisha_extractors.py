from __future__ import annotations

import json
import re
from html import unescape

SCRIPT_LD_JSON_RE = re.compile(r"<script[^>]+type=\"application/ld\+json\"[^>]*>(.*?)</script>", re.S | re.I)
SCRIPT_TAG_RE = re.compile(r"<script[^>]*>(.*?)</script>", re.S | re.I)
TAG_CLEAN_RE = re.compile(r"<[^>]+>")


def _safe_json_loads(raw_text: str) -> object | None:
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        return None


def extract_structured_payloads(html: str) -> list[dict[str, object]]:
    payloads: list[dict[str, object]] = []

    for block in SCRIPT_LD_JSON_RE.findall(html):
        data = _safe_json_loads(block.strip())
        if isinstance(data, dict):
            payloads.append(data)

    for block in SCRIPT_TAG_RE.findall(html):
        if "window.__INITIAL_STATE__" in block:
            match = re.search(r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*;", block, flags=re.S)
            if match:
                data = _safe_json_loads(match.group(1))
                if isinstance(data, dict):
                    payloads.append(data)
        if "dataLayer" in block:
            match = re.search(r"dataLayer\s*=\s*(\[.*?\])\s*;", block, flags=re.S)
            if match:
                data = _safe_json_loads(match.group(1))
                if isinstance(data, list):
                    payloads.append({"dataLayer": data})

    return payloads


def extract_by_regex_map(html: str) -> dict[str, str]:
    patterns = {
        "title": [r"<h1[^>]*>(.*?)</h1>", r'"title"\s*:\s*"(.*?)"'],
        "price": [r'"price"\s*:\s*"?([0-9\s]+)"?', r"(\d[\d\s]{3,})\s*₸"],
        "address": [r'"address"\s*:\s*"(.*?)"', r"Адрес[^<]{0,80}</div>\s*<div[^>]*>(.*?)</div>"],
        "description": [r'"description"\s*:\s*"(.*?)"', r"Описание</[^>]+>\s*<[^>]+>(.*?)</"],
        "rooms": [r'"rooms"\s*:\s*"?(\w+)"?', r"(\d+)\s*-?\s*комн"],
        "area": [r'"area"\s*:\s*"?([0-9\.,]+)"?', r"([0-9]+(?:[\.,][0-9]+)?)\s*м²"],
        "kitchen_area": [
            r"(?:кухня|площадь кухни)\D{0,20}(\d+(?:[.,]\d+)?)",
            r'"kitchen"\s*:\s*"?([0-9\.,]+)"?',
        ],
        "floor_pair": [r'"floor"\s*:\s*"?(\d+\s*/\s*\d+)"?', r"(\d+\s*/\s*\d+)\s*этаж"],
        "owner_phone": [r'"phone"\s*:\s*"(\+?[0-9\s\-\(\)]{10,20})"'],
        "image_urls": [r'"image"\s*:\s*\[(.*?)\]'],
        "characteristics": [r"Характеристики</[^>]+>\s*<[^>]+>(.*?)</", r'"details"\s*:\s*"(.*?)"'],
    }

    extracted: dict[str, str] = {}
    for key, key_patterns in patterns.items():
        for pattern in key_patterns:
            match = re.search(pattern, html, flags=re.S | re.I)
            if match and match.group(1).strip():
                extracted[key] = unescape(match.group(1).strip())
                break

    return extracted


def find_text_fallback(html: str, marker: str) -> str | None:
    plain = TAG_CLEAN_RE.sub(" ", html)
    plain = re.sub(r"\s+", " ", unescape(plain))
    idx = plain.lower().find(marker.lower())
    if idx < 0:
        return None
    return plain[idx: idx + 300]
