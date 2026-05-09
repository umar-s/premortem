"""JSON-схема ответа помощника. ТОЛЬКО валидация — не чинит и не интерпретирует."""
# /// script
# dependencies = ["jsonschema>=4.0"]
# ///
from __future__ import annotations
from typing import Any
from jsonschema import Draft202012Validator


SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["holes"],
    "properties": {
        "holes": {
            "type": "array",
            "maxItems": 2,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "title", "описание", "почему_важно", "важность",
                    "уверенность", "источник_угол",
                ],
                "properties": {
                    "title": {"type": "string", "minLength": 5, "maxLength": 120},
                    "описание": {"type": "string", "minLength": 20},
                    "почему_важно": {"type": "string", "minLength": 10},
                    "важность": {"enum": ["низкая", "средняя", "высокая"]},
                    "уверенность": {"enum": [
                        "подкреплено контекстом",
                        "требует проверки",
                        "предположение",
                    ]},
                    "источник_угол": {"type": "string", "minLength": 3},
                    "wysiati": {"type": "string"},  # опциональное расширение для угла "Будущий поддерживающий"
                },
            },
        },
        # WYSIATI на уровне ответа целиком — отдельное поле, не attribute дыры.
        # Помощник с углом "Будущий поддерживающий" обязан вернуть его даже если holes пустой.
        "wysiati": {
            "type": "string",
            "minLength": 10,
            "description": "Чьего взгляда нет в комнате; какой информации не хватает.",
        },
    },
}


_VALIDATOR = Draft202012Validator(SCHEMA)


class HelperResponseError(ValueError):
    pass


def validate(response: dict) -> None:
    errors = list(_VALIDATOR.iter_errors(response))
    if not errors:
        return
    msgs = []
    for e in errors:
        path = "/".join(str(x) for x in e.absolute_path) or "<root>"
        if e.validator == "maxItems":
            msgs.append("в ответе максимум 2 дыры")
        else:
            msgs.append(f"{path}: {e.message}")
    raise HelperResponseError("; ".join(msgs))
