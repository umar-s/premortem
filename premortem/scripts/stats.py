"""Статистика: счёт дыр по статусам."""
from __future__ import annotations
from scripts.plan_schema import Plan, HoleStatus


def summarize(plan: Plan) -> dict[str, int]:
    counts = {st.value.lower().replace(" ", "_"): 0 for st in HoleStatus}
    for h in plan.дыры:
        key = h.статус.value.lower().replace(" ", "_")
        counts[key] = counts.get(key, 0) + 1
    counts["всего"] = len(plan.дыры)
    counts["запусков"] = plan.запусков
    return counts
