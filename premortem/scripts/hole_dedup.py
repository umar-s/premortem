"""Хэш-дедуп дыр по нормализованному описанию."""
from __future__ import annotations
import hashlib
import re
from typing import Iterable


def _normalize(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def hash_description(s: str) -> str:
    return hashlib.sha256(_normalize(s).encode("utf-8")).hexdigest()


def dedup_by_hash(items: Iterable[dict], key: str = "описание") -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for item in items:
        h = hash_description(item.get(key, ""))
        if h in seen:
            continue
        seen.add(h)
        out.append(item)
    return out
