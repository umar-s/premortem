"""Тесты рендера Plan dataclass → markdown."""
from datetime import date
from scripts.plan_schema import (
    Plan, Hole, HoleStatus, Importance, Confidence, Mode,
    StatusHistoryEntry, SCHEMA_VERSION,
)
from scripts.plan_render import render_plan


def _hole_short_accepted():
    return Hole(
        id="H-001", title="клиенты не понимают ценность",
        углы=["Клиент", "Допущения"],
        найдена=date(2026, 5, 9), запуск_найдена=1,
        важность=Importance.ВЫСОКАЯ,
        уверенность=Confidence.ПОДКРЕПЛЕНО_КОНТЕКСТОМ,
        статус=HoleStatus.ПРИНЯТО, режим=Mode.КРАТКИЙ,
        описание="Целевая аудитория не понимает зачем им продукт.",
        решение={
            "что": "B: интервью с 30 клиентами",
            "почему": "понять что реально нужно",
            "первый_шаг": "написать гайд интервью",
            "исполнитель": "человек",
        },
        история_статуса=[StatusHistoryEntry(date(2026, 5, 9), HoleStatus.ПРИНЯТО, 1)],
    )


def _minimal_plan(holes=None):
    return Plan(
        plan_name="Запуск Q4", горизонт="через 3 месяца",
        создан=date(2026, 5, 9), обновлён=date(2026, 5, 9),
        запусков=1, version=SCHEMA_VERSION,
        контекст={
            "предмет": "Платный воркшоп",
            "аудитория": "Маркетинг-менеджеры",
            "успех": "50 платящих участников",
            "горизонт оценки": "через 3 месяца",
        },
        reference_class=["прошлогодний воркшоп по AI", "курсы Х"],
        дыры=holes or [],
    )


def test_render_minimal_plan_no_holes():
    p = _minimal_plan()
    text = render_plan(p)
    assert text.startswith("---\n")
    assert "plan: Запуск Q4" in text
    assert "version: '1.0'" in text
    assert "# Премортем: Запуск Q4" in text
    assert "## Контекст" in text
    assert "Предмет: Платный воркшоп" in text
    assert "## Дыры" in text


def test_render_hole_short_mode():
    h = _hole_short_accepted()
    p = _minimal_plan([h])
    text = render_plan(p)

    assert "### H-001: клиенты не понимают ценность" in text
    assert "**Угол зрения:** Клиент, Допущения" in text
    assert "**Найдена:** 2026-05-09 (запуск 1)" in text
    assert "**Важность:** высокая" in text
    assert "**Уверенность:** подкреплено контекстом" in text
    assert "**Статус:** ПРИНЯТО" in text
    assert "**Режим:** краткий" in text
    assert "B: интервью с 30 клиентами" in text
    assert "Первый шаг: написать гайд интервью" in text
    assert "Исполнитель: человек" in text
    assert "Сигнал успеха" not in text
    assert "Стоп-условие" not in text


def test_render_hole_full_mode():
    h = Hole(
        id="H-002", title="полный режим", углы=["Исполнитель"],
        найдена=date(2026, 5, 9), запуск_найдена=1,
        важность=Importance.ВЫСОКАЯ,
        уверенность=Confidence.ПОДКРЕПЛЕНО_КОНТЕКСТОМ,
        статус=HoleStatus.ПРИНЯТО, режим=Mode.ПОЛНЫЙ,
        описание="...",
        решение={
            "что": "X", "почему": "Y",
            "prevent": ["шаг 1", "шаг 2", "шаг 3"],
            "detect": "сигнал успеха",
            "стоп_условие": "стоп",
            "limit_damage": "если случилось",
            "исполнитель": "агент",
            "открытые_вопросы": ["вопрос 1"],
        },
        история_статуса=[],
    )
    text = render_plan(_minimal_plan([h]))
    assert "Сигнал успеха (detect): сигнал успеха" in text
    assert "Стоп-условие: стоп" in text
    assert "Если уже случилось (limit damage): если случилось" in text
    assert "1. шаг 1" in text


def test_render_includes_top_and_bias():
    h = _hole_short_accepted()
    p = _minimal_plan([h])
    p.топ = ["H-001"]
    p.bias_проверка = {
        "риск": "overconfidence",
        "коррекция": "добавить 50% к оценке времени",
    }
    text = render_plan(p)
    assert "## Топ 1–3 — с чего начать" in text
    assert "**H-001**" in text
    assert "### Bias-проверка топа" in text
    assert "overconfidence" in text


def test_render_includes_reverse_premortem_when_present():
    p = _minimal_plan()
    p.reverse_премортем = {
        "причины": ["рынок ушёл", "конкурент захватил", "команда выгорела ждать"],
        "перевешивает": "риски основного плана сильнее",
    }
    text = render_plan(p)
    assert "## Reverse премортем" in text
    assert "1. рынок ушёл" in text
    assert "**Что перевешивает:** риски основного плана сильнее" in text


def test_render_omits_reverse_premortem_when_none():
    p = _minimal_plan()
    text = render_plan(p)
    assert "## Reverse премортем" not in text
