import pytest
from scripts.validate_helper_response import validate, HelperResponseError


_VALID = {
    "holes": [
        {
            "title": "клиенты не понимают ценность",
            "описание": "Целевая аудитория не понимает зачем им продукт.",
            "почему_важно": "без понимания продукта нет конверсии",
            "важность": "высокая",
            "уверенность": "подкреплено контекстом",
            "источник_угол": "Клиент",
        }
    ]
}


def test_valid_response_passes():
    validate(_VALID)


def test_empty_holes_list_is_valid():
    validate({"holes": []})


def test_too_many_holes_fails():
    bad = {"holes": [
        {"title": str(i), "описание": "x", "почему_важно": "y",
         "важность": "средняя", "уверенность": "предположение",
         "источник_угол": "Клиент"} for i in range(3)
    ]}
    with pytest.raises(HelperResponseError, match="максимум 2"):
        validate(bad)


def test_missing_required_field_fails():
    bad = {"holes": [{
        "title": "x", "описание": "y", "почему_важно": "z",
        "важность": "высокая", "уверенность": "предположение",
        # пропущено источник_угол
    }]}
    with pytest.raises(HelperResponseError):
        validate(bad)


def test_invalid_enum_fails():
    bad = {"holes": [{
        "title": "x", "описание": "y", "почему_важно": "z",
        "важность": "huge",  # неверное значение
        "уверенность": "предположение", "источник_угол": "Клиент",
    }]}
    with pytest.raises(HelperResponseError):
        validate(bad)


def test_validate_only_does_not_fix():
    """Валидатор только проверяет; не возвращает 'починенный' ответ."""
    bad = {"holes": [{"title": "x"}]}
    with pytest.raises(HelperResponseError):
        validate(bad)
