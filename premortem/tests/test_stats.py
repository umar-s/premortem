from datetime import date
from scripts.plan_schema import (
    Plan, Hole, HoleStatus, Importance, Confidence, Mode, SCHEMA_VERSION,
)
from scripts.stats import summarize


def _hole(id_, статус):
    return Hole(
        id=id_, title="x", углы=["Клиент"], найдена=date(2026, 5, 9),
        запуск_найдена=1, важность=Importance.СРЕДНЯЯ,
        уверенность=Confidence.ТРЕБУЕТ_ПРОВЕРКИ, статус=статус,
        режим=Mode.КРАТКИЙ, описание="x",
        решение={"что": "А", "почему": "Б", "первый_шаг": "В", "исполнитель": "агент"} if статус == HoleStatus.ПРИНЯТО else None,
        история_статуса=[],
    )


def test_summarize_counts_by_status():
    p = Plan(
        plan_name="x", горизонт="y", создан=date(2026, 5, 9),
        обновлён=date(2026, 5, 9), запусков=2, version=SCHEMA_VERSION,
        контекст={}, reference_class=[],
        дыры=[
            _hole("H-001", HoleStatus.ПРИНЯТО),
            _hole("H-002", HoleStatus.ПРИНЯТО),
            _hole("H-003", HoleStatus.ОТЛОЖЕНО),
            _hole("H-004", HoleStatus.В_РАБОТЕ),
        ],
    )
    s = summarize(p)
    assert s["всего"] == 4
    assert s["принято"] == 2
    assert s["отложено"] == 1
    assert s["в_работе"] == 1
    assert s["запусков"] == 2
