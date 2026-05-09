from datetime import date
from scripts.plan_schema import Hole, HoleStatus, Importance, Confidence, Mode
from scripts.sort_holes import sort_holes


def _h(id_, статус, важность, найдена):
    return Hole(
        id=id_, title="x", углы=["Клиент"], найдена=найдена,
        запуск_найдена=1, важность=важность,
        уверенность=Confidence.ТРЕБУЕТ_ПРОВЕРКИ, статус=статус,
        режим=Mode.КРАТКИЙ, описание="x",
        решение={"что":"А","почему":"Б","первый_шаг":"В","исполнитель":"агент"} if статус == HoleStatus.ПРИНЯТО else None,
        история_статуса=[],
    )


def test_sort_active_first_then_by_importance_then_by_date():
    h1 = _h("H-003", HoleStatus.ОТВЕРГНУТО, Importance.ВЫСОКАЯ, date(2026, 5, 9))
    h2 = _h("H-001", HoleStatus.ПРИНЯТО, Importance.СРЕДНЯЯ, date(2026, 5, 1))
    h3 = _h("H-002", HoleStatus.ПРИНЯТО, Importance.ВЫСОКАЯ, date(2026, 5, 5))
    h4 = _h("H-004", HoleStatus.ОТЛОЖЕНО, Importance.НИЗКАЯ, date(2026, 5, 9))
    sorted_ = sort_holes([h1, h2, h3, h4])
    assert [h.id for h in sorted_] == ["H-002", "H-001", "H-004", "H-003"]
