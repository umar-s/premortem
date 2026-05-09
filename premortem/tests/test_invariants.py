"""Инварианты round-trip: parse(render(p)) == p для 10 репрезентативных планов."""
import pytest
from datetime import date
from scripts.plan_schema import (
    Plan, Hole, HoleStatus, Importance, Confidence, Mode,
    StatusHistoryEntry, SessionRecommendation, RerunStatus, SCHEMA_VERSION, validate_plan,
)
from scripts.plan_render import render_plan
from scripts.plan_parse import parse_plan


# ---------------------------------------------------------------------------
# Вспомогательные строительные блоки
# ---------------------------------------------------------------------------

def _short_hole(
    hid="H-001",
    title="дыра краткий режим",
    углы=None,
    статус=HoleStatus.ПРИНЯТО,
    важность=Importance.ВЫСОКАЯ,
    уверенность=Confidence.ПОДКРЕПЛЕНО_КОНТЕКСТОМ,
    описание="описание дыры",
    решение=None,
    история=None,
    причина_отказа=None,
):
    if углы is None:
        углы = ["Клиент"]
    if решение is None and статус != HoleStatus.ОТВЕРГНУТО:
        решение = {
            "что": "вариант А",
            "почему": "потому что это важно",
            "первый_шаг": "первый конкретный шаг",
            "исполнитель": "агент",
        }
    if история is None:
        история = [StatusHistoryEntry(date(2026, 5, 9), статус, 1)]
    return Hole(
        id=hid, title=title, углы=углы,
        найдена=date(2026, 5, 9), запуск_найдена=1,
        важность=важность, уверенность=уверенность,
        статус=статус, режим=Mode.КРАТКИЙ,
        описание=описание, решение=решение,
        история_статуса=история,
        причина_отказа=причина_отказа,
    )


def _full_hole(
    hid="H-002",
    title="дыра полный режим",
    углы=None,
    статус=HoleStatus.ПРИНЯТО,
):
    if углы is None:
        углы = ["Исполнитель", "Ресурсы"]
    return Hole(
        id=hid, title=title, углы=углы,
        найдена=date(2026, 5, 9), запуск_найдена=1,
        важность=Importance.ВЫСОКАЯ,
        уверенность=Confidence.ТРЕБУЕТ_ПРОВЕРКИ,
        статус=статус, режим=Mode.ПОЛНЫЙ,
        описание="полное описание дыры",
        решение={
            "что": "полное решение X",
            "почему": "стратегический выбор Y",
            "prevent": ["шаг первый", "шаг второй", "шаг третий"],
            "detect": "сигнал что сработало",
            "стоп_условие": "когда останавливаемся",
            "limit_damage": "если уже случилось делаем так",
            "исполнитель": "оба",
            "открытые_вопросы": ["что если X сорвётся", "кто проверит детект"],
        },
        история_статуса=[StatusHistoryEntry(date(2026, 5, 9), статус, 1)],
    )


def _base_plan(**kwargs) -> Plan:
    defaults = dict(
        plan_name="Тест-план",
        горизонт="через 6 месяцев",
        создан=date(2026, 5, 9),
        обновлён=date(2026, 5, 9),
        запусков=1,
        version=SCHEMA_VERSION,
        контекст={
            "предмет": "продукт Х",
            "аудитория": "команда разработки",
            "успех": "выпуск v1.0",
            "горизонт оценки": "через 6 месяцев",
        },
        reference_class=["проект А", "проект Б"],
        дыры=[],
    )
    defaults.update(kwargs)
    return Plan(**defaults)


# ---------------------------------------------------------------------------
# 10 планов-фикстур
# ---------------------------------------------------------------------------

def _plan_1_minimal_no_holes() -> Plan:
    """1. Минимальный план без дыр."""
    return _base_plan()


def _plan_2_single_short_accepted() -> Plan:
    """2. Одна дыра, краткий режим, статус ПРИНЯТО."""
    return _base_plan(дыры=[_short_hole()])


def _plan_3_single_full_accepted() -> Plan:
    """3. Одна дыра, полный режим, статус ПРИНЯТО."""
    return _base_plan(дыры=[_full_hole()])


def _plan_4_rejected_hole() -> Plan:
    """4. Дыра ОТВЕРГНУТО с причиной отказа."""
    h = _short_hole(
        статус=HoleStatus.ОТВЕРГНУТО,
        решение=None,
        история=[StatusHistoryEntry(date(2026, 5, 9), HoleStatus.ОТВЕРГНУТО, 1)],
        причина_отказа="риск недостаточно значимый для текущего горизонта",
    )
    return _base_plan(дыры=[h])


def _plan_5_with_top_and_bias() -> Plan:
    """5. Дыры + топ + bias-проверка."""
    return _base_plan(
        дыры=[_short_hole()],
        топ=["H-001"],
        bias_проверка={
            "риск": "overconfidence",
            "коррекция": "добавить 50% к оценке времени",
        },
    )


def _plan_6_with_reverse() -> Plan:
    """6. Reverse премортем присутствует (требует session_recommendation in {reduce_stake, delay, abort})."""
    return _base_plan(
        reverse_премортем={
            "причины": ["рынок ушёл", "конкурент захватил нишу"],
            "перевешивает": "риски основного плана сильнее",
        },
        session_recommendation=SessionRecommendation.DELAY,
    )


def _plan_7_session_recommendation() -> Plan:
    """7. session_recommendation = abort."""
    return _base_plan(
        дыры=[_short_hole()],
        session_recommendation=SessionRecommendation.ABORT,
    )


def _plan_8_multi_holes_mixed_modes() -> Plan:
    """8. Несколько дыр с разными режимами и статусами."""
    h1 = _short_hole(hid="H-001", title="первая краткая", статус=HoleStatus.ПРИНЯТО)
    h2 = _full_hole(hid="H-002", title="вторая полная", статус=HoleStatus.ПРИНЯТО)
    h3 = _short_hole(
        hid="H-003", title="третья отложена",
        статус=HoleStatus.ОТЛОЖЕНО,
        решение=None,
        история=[StatusHistoryEntry(date(2026, 5, 9), HoleStatus.ОТЛОЖЕНО, 1)],
    )
    return _base_plan(дыры=[h1, h2, h3], топ=["H-001", "H-002"])


def _plan_9_history_with_comment() -> Plan:
    """9. История статуса с комментарием."""
    h = _short_hole(
        история=[
            StatusHistoryEntry(date(2026, 5, 1), HoleStatus.ОТКРЫТА, 1),
            StatusHistoryEntry(
                date(2026, 5, 9), HoleStatus.ПРИНЯТО, 1,
                комментарий="решили взять после ревью с командой",
            ),
        ],
    )
    return _base_plan(дыры=[h])


def _plan_10_full_featured() -> Plan:
    """10. Полный набор: дыры, топ, bias, reverse, session_recommendation."""
    h1 = _short_hole(hid="H-001", title="краткая принята")
    h2 = _full_hole(hid="H-002", title="полная принята")
    h3 = Hole(
        id="H-003", title="закрытая дыра",
        углы=["Рынок"],
        найдена=date(2026, 5, 9), запуск_найдена=1,
        важность=Importance.СРЕДНЯЯ,
        уверенность=Confidence.ПРЕДПОЛОЖЕНИЕ,
        статус=HoleStatus.ЗАКРЫТА, режим=Mode.КРАТКИЙ,
        описание="было решено в прошлом запуске",
        решение={
            "что": "закрыли вариантом Б",
            "почему": "проверили гипотезу",
            "первый_шаг": "нет — уже сделано",
            "исполнитель": "человек",
        },
        история_статуса=[StatusHistoryEntry(date(2026, 5, 9), HoleStatus.ЗАКРЫТА, 1)],
    )
    return _base_plan(
        дыры=[h1, h2, h3],
        топ=["H-001", "H-002"],
        bias_проверка={"риск": "sunk cost", "коррекция": "переоценить с нуля"},
        reverse_премортем={
            "причины": ["регуляторные ограничения", "финансирование не пришло"],
            "перевешивает": "шансы успеха выше рисков",
        },
        session_recommendation=SessionRecommendation.DELAY,
    )


def _multiline_desc_hole():
    h = _short_hole(hid="H-101", title="дыра с многоабзацным описанием")
    h.описание = (
        "первая строка описания\n"
        "продолжение в той же строке\n"
        "\n"
        "новый абзац после пустой строки\n"
        "\n"
        "третий абзац"
    )
    return h


def _plan_11_multiline_description() -> Plan:
    """11. Многострочное описание дыры (golden case из плана требований)."""
    return _base_plan(дыры=[_multiline_desc_hole()])


def _plan_12_merged_from_and_rerun() -> Plan:
    """12. Дыра с заполненными merged_from и rerun_status (golden case для codex fix #1)."""
    h = Hole(
        id="H-001", title="дыра с дедупом и rerun-маркером",
        углы=["Клиент", "Рынок"],
        найдена=date(2026, 5, 9), запуск_найдена=1,
        важность=Importance.ВЫСОКАЯ,
        уверенность=Confidence.ТРЕБУЕТ_ПРОВЕРКИ,
        статус=HoleStatus.ПРИНЯТО, режим=Mode.КРАТКИЙ,
        описание="описание дыры возникшей из дедупа",
        решение={
            "что": "решение дедупнутой дыры",
            "почему": "объединили два схожих риска",
            "первый_шаг": "первый конкретный шаг",
            "исполнитель": "агент",
        },
        история_статуса=[StatusHistoryEntry(date(2026, 5, 9), HoleStatus.ПРИНЯТО, 2)],
        merged_from=["H-003", "H-007"],
        rerun_status=RerunStatus.NEW_ASPECT,
    )
    return _base_plan(дыры=[h])


# ---------------------------------------------------------------------------
# Параметризованные инварианты
# ---------------------------------------------------------------------------

PLANS = [
    ("01_minimal_no_holes",          _plan_1_minimal_no_holes),
    ("02_single_short_accepted",     _plan_2_single_short_accepted),
    ("03_single_full_accepted",      _plan_3_single_full_accepted),
    ("04_rejected_hole",             _plan_4_rejected_hole),
    ("05_top_and_bias",              _plan_5_with_top_and_bias),
    ("06_reverse_premortem",         _plan_6_with_reverse),
    ("07_session_recommendation",    _plan_7_session_recommendation),
    ("08_multi_holes_mixed_modes",   _plan_8_multi_holes_mixed_modes),
    ("09_history_with_comment",      _plan_9_history_with_comment),
    ("10_full_featured",             _plan_10_full_featured),
    ("11_multiline_description",     _plan_11_multiline_description),
    ("12_merged_from_and_rerun",     _plan_12_merged_from_and_rerun),
]


@pytest.mark.parametrize("name,factory", PLANS, ids=[p[0] for p in PLANS])
def test_round_trip(name: str, factory):
    """parse(render(p)) == p для каждого репрезентативного плана."""
    original = factory()
    validate_plan(original)  # убедимся, что фикстура сама валидна

    rendered = render_plan(original)
    parsed = parse_plan(rendered)

    # --- frontmatter поля ---
    assert parsed.plan_name == original.plan_name, "plan_name"
    assert parsed.горизонт == original.горизонт, "горизонт"
    assert parsed.создан == original.создан, "создан"
    assert parsed.обновлён == original.обновлён, "обновлён"
    assert parsed.запусков == original.запусков, "запусков"
    assert parsed.version == original.version, "version"
    assert parsed.session_recommendation == original.session_recommendation, "session_recommendation"

    # --- контекст ---
    assert parsed.контекст == original.контекст, "контекст"
    assert parsed.reference_class == original.reference_class, "reference_class"

    # --- дыры ---
    assert len(parsed.дыры) == len(original.дыры), "количество дыр"
    for orig_h, parsed_h in zip(original.дыры, parsed.дыры):
        _assert_hole_eq(orig_h, parsed_h)

    # --- топ / bias / reverse ---
    assert parsed.топ == original.топ, "топ"
    assert parsed.bias_проверка == original.bias_проверка, "bias_проверка"
    assert parsed.reverse_премортем == original.reverse_премортем, "reverse_премортем"


def _assert_hole_eq(orig: Hole, parsed: Hole) -> None:
    prefix = orig.id
    assert parsed.id == orig.id, f"{prefix}: id"
    assert parsed.title == orig.title, f"{prefix}: title"
    assert parsed.углы == orig.углы, f"{prefix}: углы"
    assert parsed.найдена == orig.найдена, f"{prefix}: найдена"
    assert parsed.запуск_найдена == orig.запуск_найдена, f"{prefix}: запуск_найдена"
    assert parsed.важность == orig.важность, f"{prefix}: важность"
    assert parsed.уверенность == orig.уверенность, f"{prefix}: уверенность"
    assert parsed.статус == orig.статус, f"{prefix}: статус"
    assert parsed.режим == orig.режим, f"{prefix}: режим"
    assert parsed.описание == orig.описание, f"{prefix}: описание"
    assert parsed.причина_отказа == orig.причина_отказа, f"{prefix}: причина_отказа"
    assert parsed.решение == orig.решение, f"{prefix}: решение"
    assert len(parsed.история_статуса) == len(orig.история_статуса), f"{prefix}: len(история)"
    for i, (oh, ph) in enumerate(zip(orig.история_статуса, parsed.история_статуса)):
        assert ph.дата == oh.дата, f"{prefix}: история[{i}].дата"
        assert ph.статус == oh.статус, f"{prefix}: история[{i}].статус"
        assert ph.запуск == oh.запуск, f"{prefix}: история[{i}].запуск"
        assert ph.комментарий == oh.комментарий, f"{prefix}: история[{i}].комментарий"
    assert parsed.merged_from == orig.merged_from, f"{prefix}: merged_from"
    assert parsed.rerun_status == orig.rerun_status, f"{prefix}: rerun_status"
