"""Тесты схемы данных премортема."""
import pytest
from datetime import date
from scripts.plan_schema import (
    Plan, Hole, ResolutionShort, ResolutionFull, StatusHistoryEntry,
    HoleStatus, Importance, Confidence, Mode, SessionRecommendation,
    SCHEMA_VERSION,
    validate_plan, ValidationError,
)


def test_schema_version_is_string():
    assert isinstance(SCHEMA_VERSION, str)
    assert SCHEMA_VERSION == "1.0"


def test_minimal_plan_validates():
    p = Plan(
        plan_name="test plan",
        горизонт="через 3 месяца",
        создан=date(2026, 5, 9),
        обновлён=date(2026, 5, 9),
        запусков=1,
        version=SCHEMA_VERSION,
        контекст={"предмет": "X", "аудитория": "Y", "успех": "Z", "горизонт оценки": "через 3 месяца"},
        reference_class=["похожий проект A"],
        дыры=[],
    )
    validate_plan(p)


def test_hole_with_short_resolution_validates():
    h = Hole(
        id="H-001",
        title="дыра",
        углы=["Клиент"],
        найдена=date(2026, 5, 9),
        запуск_найдена=1,
        важность=Importance.ВЫСОКАЯ,
        уверенность=Confidence.ПОДКРЕПЛЕНО_КОНТЕКСТОМ,
        статус=HoleStatus.ПРИНЯТО,
        режим=Mode.КРАТКИЙ,
        описание="абзац",
        решение={"что": "...", "почему": "...", "первый_шаг": "...", "исполнитель": "агент"},
        история_статуса=[StatusHistoryEntry(дата=date(2026, 5, 9), статус=HoleStatus.ПРИНЯТО, запуск=1)],
    )
    p = _make_minimal_plan_with(h)
    validate_plan(p)


def test_hole_full_mode_requires_full_resolution_fields():
    h = Hole(
        id="H-001", title="дыра", углы=["Клиент"], найдена=date(2026, 5, 9),
        запуск_найдена=1, важность=Importance.ВЫСОКАЯ,
        уверенность=Confidence.ПОДКРЕПЛЕНО_КОНТЕКСТОМ,
        статус=HoleStatus.ПРИНЯТО, режим=Mode.ПОЛНЫЙ, описание="...",
        решение={"что": "...", "почему": "..."},  # неполный — нет prevent/detect/limit
        история_статуса=[],
    )
    p = _make_minimal_plan_with(h)
    with pytest.raises(ValidationError, match="полный режим требует"):
        validate_plan(p)


def test_duplicate_hole_id_fails():
    h1 = _make_simple_hole("H-001")
    h2 = _make_simple_hole("H-001")
    p = Plan(
        plan_name="x", горизонт="через 30 дней",
        создан=date(2026, 5, 9), обновлён=date(2026, 5, 9),
        запусков=1, version=SCHEMA_VERSION,
        контекст={}, reference_class=[], дыры=[h1, h2],
    )
    with pytest.raises(ValidationError, match="дублирующийся ID"):
        validate_plan(p)


def test_invalid_hole_id_format_fails():
    h = _make_simple_hole("Bad-1")
    p = _make_minimal_plan_with(h)
    with pytest.raises(ValidationError, match="формат ID"):
        validate_plan(p)


def test_hole_short_mode_requires_short_resolution_fields():
    h = Hole(
        id="H-001", title="дыра", углы=["Клиент"], найдена=date(2026, 5, 9),
        запуск_найдена=1, важность=Importance.ВЫСОКАЯ,
        уверенность=Confidence.ПОДКРЕПЛЕНО_КОНТЕКСТОМ,
        статус=HoleStatus.ПРИНЯТО, режим=Mode.КРАТКИЙ, описание="...",
        решение={"что": "...", "почему": "..."},  # нет первый_шаг и исполнитель
        история_статуса=[],
    )
    p = _make_minimal_plan_with(h)
    with pytest.raises(ValidationError, match="краткий режим требует"):
        validate_plan(p)


def test_hole_rejected_status_requires_rejection_reason():
    h = Hole(
        id="H-001", title="дыра", углы=["Клиент"], найдена=date(2026, 5, 9),
        запуск_найдена=1, важность=Importance.СРЕДНЯЯ,
        уверенность=Confidence.ТРЕБУЕТ_ПРОВЕРКИ,
        статус=HoleStatus.ОТВЕРГНУТО, режим=Mode.КРАТКИЙ, описание="...",
        решение=None, причина_отказа=None, история_статуса=[],
    )
    p = _make_minimal_plan_with(h)
    with pytest.raises(ValidationError, match="ОТВЕРГНУТО"):
        validate_plan(p)


def test_unsupported_version_fails():
    p = Plan(
        plan_name="x", горизонт="через 30 дней",
        создан=date(2026, 5, 9), обновлён=date(2026, 5, 9),
        запусков=1, version="999.0",
        контекст={}, reference_class=[], дыры=[],
    )
    with pytest.raises(ValidationError, match="неподдерживаемая версия"):
        validate_plan(p)


def _make_simple_hole(id_):
    return Hole(
        id=id_, title="x", углы=["Клиент"], найдена=date(2026, 5, 9),
        запуск_найдена=1, важность=Importance.СРЕДНЯЯ,
        уверенность=Confidence.ТРЕБУЕТ_ПРОВЕРКИ,
        статус=HoleStatus.ОТЛОЖЕНО, режим=Mode.КРАТКИЙ, описание="x",
        решение=None, история_статуса=[],
    )


def _make_accepted_hole(id_):
    """Дыра со статусом ПРИНЯТО и минимальным решением."""
    return Hole(
        id=id_, title="x", углы=["Клиент"], найдена=date(2026, 5, 9),
        запуск_найдена=1, важность=Importance.ВЫСОКАЯ,
        уверенность=Confidence.ПОДКРЕПЛЕНО_КОНТЕКСТОМ,
        статус=HoleStatus.ПРИНЯТО, режим=Mode.КРАТКИЙ, описание="x",
        решение={"что": "...", "почему": "...", "первый_шаг": "...", "исполнитель": "агент"},
        история_статуса=[],
    )


def _make_minimal_plan_with(hole):
    return Plan(
        plan_name="x", горизонт="через 30 дней",
        создан=date(2026, 5, 9), обновлён=date(2026, 5, 9),
        запусков=1, version=SCHEMA_VERSION,
        контекст={}, reference_class=[], дыры=[hole],
    )


# ── Phase 3 инварианты ────────────────────────────────────────────────────────


def test_top_max_three():
    """топ не может содержать более 3 дыр."""
    holes = [_make_accepted_hole(f"H-{i:03d}") for i in range(1, 5)]
    p = Plan(
        plan_name="x", горизонт="через 30 дней",
        создан=date(2026, 5, 9), обновлён=date(2026, 5, 9),
        запусков=1, version=SCHEMA_VERSION,
        контекст={}, reference_class=[],
        дыры=holes,
        топ=["H-001", "H-002", "H-003", "H-004"],  # 4 > 3
    )
    with pytest.raises(ValidationError, match="топ содержит более 3"):
        validate_plan(p)


def test_top_only_on_accepted_or_in_progress():
    """топ может содержать только дыры со статусом ПРИНЯТО или В_РАБОТЕ."""
    h_rejected = Hole(
        id="H-001", title="x", углы=["Клиент"], найдена=date(2026, 5, 9),
        запуск_найдена=1, важность=Importance.ВЫСОКАЯ,
        уверенность=Confidence.ТРЕБУЕТ_ПРОВЕРКИ,
        статус=HoleStatus.ОТЛОЖЕНО, режим=Mode.КРАТКИЙ, описание="x",
        решение=None, история_статуса=[],
    )
    p = Plan(
        plan_name="x", горизонт="через 30 дней",
        создан=date(2026, 5, 9), обновлён=date(2026, 5, 9),
        запусков=1, version=SCHEMA_VERSION,
        контекст={}, reference_class=[],
        дыры=[h_rejected],
        топ=["H-001"],  # ОТЛОЖЕНО — недопустимо в топе
    )
    with pytest.raises(ValidationError, match="топ может содержать только"):
        validate_plan(p)


def test_bias_requires_top():
    """bias_проверка не может быть указан при пустом топе."""
    p = Plan(
        plan_name="x", горизонт="через 30 дней",
        создан=date(2026, 5, 9), обновлён=date(2026, 5, 9),
        запусков=1, version=SCHEMA_VERSION,
        контекст={}, reference_class=[], дыры=[],
        топ=[],
        bias_проверка={"риск": "overconfidence", "коррекция": "добавить буфер"},
    )
    with pytest.raises(ValidationError, match="bias_проверка указан но топ пуст"):
        validate_plan(p)


def test_reverse_only_on_reduce_delay_abort():
    """reverse_премортем допустим только при session_recommendation в {reduce_stake, delay, abort}."""
    p = Plan(
        plan_name="x", горизонт="через 30 дней",
        создан=date(2026, 5, 9), обновлён=date(2026, 5, 9),
        запусков=1, version=SCHEMA_VERSION,
        контекст={}, reference_class=[], дыры=[],
        session_recommendation=SessionRecommendation.CONTINUE,
        reverse_премортем={"причины": ["A", "B", "C"], "перевешивает": "нет"},
    )
    with pytest.raises(ValidationError, match="reverse_премортем требует session_recommendation"):
        validate_plan(p)


def test_zero_accepted_means_empty_top():
    """Если нет дыр со статусом ПРИНЯТО или В_РАБОТЕ, топ должен быть пустым."""
    h_deferred = Hole(
        id="H-001", title="x", углы=["Клиент"], найдена=date(2026, 5, 9),
        запуск_найдена=1, важность=Importance.СРЕДНЯЯ,
        уверенность=Confidence.ТРЕБУЕТ_ПРОВЕРКИ,
        статус=HoleStatus.ОТЛОЖЕНО, режим=Mode.КРАТКИЙ, описание="x",
        решение=None, история_статуса=[],
    )
    # H-001 — ОТЛОЖЕНО, но указана в топе (нарушение)
    p = Plan(
        plan_name="x", горизонт="через 30 дней",
        создан=date(2026, 5, 9), обновлён=date(2026, 5, 9),
        запусков=1, version=SCHEMA_VERSION,
        контекст={}, reference_class=[],
        дыры=[h_deferred],
        топ=["H-001"],
    )
    # Это нарушает инвариант 2 (топ только на ПРИНЯТО/В_РАБОТЕ),
    # который покрывает и инвариант 5. Проверяем что ошибка поднимается.
    with pytest.raises(ValidationError):
        validate_plan(p)
