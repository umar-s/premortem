"""Безопасный slug из произвольной строки (RU/EN/цифры). Только [a-z0-9-]."""
from __future__ import annotations
import re


_TRANSLIT_TABLE = str.maketrans({
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "zh", "з": "z", "и": "i", "й": "j", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
})


def slugify(s: str, max_len: int = 64) -> str:
    if not s:
        raise ValueError("пустая строка не имеет slug'а")
    s = s.lower().translate(_TRANSLIT_TABLE)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    s = re.sub(r"-+", "-", s)
    if not s:
        raise ValueError("после очистки пусто")
    return s[:max_len].rstrip("-")
