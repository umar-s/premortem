"""Тесты parse: markdown → Plan."""
import pytest
from datetime import date
from scripts.plan_schema import (
    HoleStatus, Importance, Confidence, Mode, SCHEMA_VERSION,
    Plan, Hole, StatusHistoryEntry,
)
from scripts.plan_parse import parse_plan, ParseError
from scripts.plan_render import render_plan


def _build_plan_with_short_hole():
    return Plan(
        plan_name="Запуск Q4", горизонт="через 3 месяца",
        создан=date(2026, 5, 9), обновлён=date(2026, 5, 9),
        запусков=1, version=SCHEMA_VERSION,
        контекст={"предмет": "X", "аудитория": "Y", "успех": "Z",
                  "горизонт оценки": "через 3 месяца"},
        reference_class=["проект А"],
        дыры=[
            Hole(
                id="H-001", title="дыра один", углы=["Клиент"],
                найдена=date(2026, 5, 9), запуск_найдена=1,
                важность=Importance.ВЫСОКАЯ,
                уверенность=Confidence.ПОДКРЕПЛЕНО_КОНТЕКСТОМ,
                статус=HoleStatus.ПРИНЯТО, режим=Mode.КРАТКИЙ,
                описание="абзац",
                решение={"что": "вариант А", "почему": "потому что",
                         "первый_шаг": "первый шаг", "исполнитель": "агент"},
                история_статуса=[
                    StatusHistoryEntry(date(2026, 5, 9), HoleStatus.ПРИНЯТО, 1)
                ],
            )
        ],
    )


def test_parse_minimal_plan():
    text = render_plan(_build_plan_with_short_hole())
    p = parse_plan(text)
    assert p.plan_name == "Запуск Q4"
    assert p.горизонт == "через 3 месяца"
    assert p.запусков == 1
    assert len(p.дыры) == 1


def test_parse_short_hole_fields():
    p = parse_plan(render_plan(_build_plan_with_short_hole()))
    h = p.дыры[0]
    assert h.id == "H-001"
    assert h.title == "дыра один"
    assert h.углы == ["Клиент"]
    assert h.важность == Importance.ВЫСОКАЯ
    assert h.уверенность == Confidence.ПОДКРЕПЛЕНО_КОНТЕКСТОМ
    assert h.статус == HoleStatus.ПРИНЯТО
    assert h.режим == Mode.КРАТКИЙ
    assert h.решение["что"] == "вариант А"
    assert h.решение["первый_шаг"] == "первый шаг"


def test_parse_garbage_raises():
    with pytest.raises(ParseError):
        parse_plan("# Just a body, no frontmatter")


def test_invalid_rerun_status_raises_validation_error():
    """Невалидное значение Rerun должно бросать ParseError (оборачивает ValidationError)."""
    text = render_plan(_build_plan_with_short_hole())
    bad_text = text.replace(
        "- **Угол зрения:** Клиент",
        "- **Rerun:** not-a-valid-status\n- **Угол зрения:** Клиент",
    )
    with pytest.raises(ParseError):
        parse_plan(bad_text)
