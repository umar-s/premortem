"""Детерминированная сортировка дыр для рендера."""
from __future__ import annotations
from scripts.plan_schema import Hole, HoleStatus, Importance


_STATUS_RANK = {
    HoleStatus.В_РАБОТЕ: 0,
    HoleStatus.ПРИНЯТО: 0,
    HoleStatus.ОТКРЫТА: 0,
    HoleStatus.ОТЛОЖЕНО: 1,
    HoleStatus.ОТВЕРГНУТО: 2,
    HoleStatus.ЗАКРЫТА: 3,
}

_IMPORTANCE_RANK = {
    Importance.ВЫСОКАЯ: 0, Importance.СРЕДНЯЯ: 1, Importance.НИЗКАЯ: 2,
}


def sort_holes(holes: list[Hole]) -> list[Hole]:
    return sorted(
        holes,
        key=lambda h: (
            _STATUS_RANK.get(h.статус, 9),
            _IMPORTANCE_RANK.get(h.важность, 9),
            h.найдена.toordinal(),
            h.id,
        ),
    )
