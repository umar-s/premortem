"""Схема данных премортем-плана: dataclasses, enum'ы, валидатор."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any, TypedDict, NotRequired
import re


SCHEMA_VERSION = "1.0"
HOLE_ID_PATTERN = re.compile(r"^H-\d{3,}$")


class HoleStatus(str, Enum):
    ОТКРЫТА = "ОТКРЫТА"
    ПРИНЯТО = "ПРИНЯТО"
    ОТЛОЖЕНО = "ОТЛОЖЕНО"
    ОТВЕРГНУТО = "ОТВЕРГНУТО"
    В_РАБОТЕ = "В РАБОТЕ"
    ЗАКРЫТА = "ЗАКРЫТА"


class Importance(str, Enum):
    НИЗКАЯ = "низкая"
    СРЕДНЯЯ = "средняя"
    ВЫСОКАЯ = "высокая"


class Confidence(str, Enum):
    ПОДКРЕПЛЕНО_КОНТЕКСТОМ = "подкреплено контекстом"
    ТРЕБУЕТ_ПРОВЕРКИ = "требует проверки"
    ПРЕДПОЛОЖЕНИЕ = "предположение"


class Mode(str, Enum):
    КРАТКИЙ = "краткий"
    ПОЛНЫЙ = "полный"


class SessionRecommendation(str, Enum):
    CONTINUE = "continue"
    REDUCE_STAKE = "reduce_stake"
    DELAY = "delay"
    ABORT = "abort"


class RerunStatus(str, Enum):
    SAME = "same"
    WORSE = "worse"
    RESOLVED = "resolved"
    NEW = "new"
    NEW_ASPECT = "new-aspect"


class ResolutionShort(TypedDict):
    что: str
    почему: str
    первый_шаг: str
    исполнитель: str  # "агент" | "человек" | "оба"


class ResolutionFull(TypedDict):
    что: str
    почему: str
    prevent: list[str]  # 2–3 первых шага
    detect: str  # сигнал успеха
    стоп_условие: str
    limit_damage: str
    исполнитель: str
    открытые_вопросы: NotRequired[list[str]]


@dataclass
class StatusHistoryEntry:
    дата: date
    статус: HoleStatus
    запуск: int
    комментарий: str | None = None


@dataclass
class Hole:
    id: str
    title: str
    углы: list[str]
    найдена: date
    запуск_найдена: int
    важность: Importance
    уверенность: Confidence
    статус: HoleStatus
    режим: Mode
    описание: str
    решение: dict[str, Any] | None
    история_статуса: list[StatusHistoryEntry] = field(default_factory=list)
    причина_отказа: str | None = None  # только для ОТВЕРГНУТО
    merged_from: list[str] = field(default_factory=list)  # ID дыр-источников при семантическом дедупе
    rerun_status: RerunStatus | None = None  # only on rerun


@dataclass
class Plan:
    plan_name: str
    горизонт: str
    создан: date
    обновлён: date
    запусков: int
    version: str
    контекст: dict[str, str]
    reference_class: list[str]
    дыры: list[Hole]
    топ: list[str] = field(default_factory=list)  # ["H-001", "H-005", "H-007"]
    bias_проверка: dict[str, str] | None = None  # {"риск": "...", "коррекция": "..."}
    reverse_премортем: dict[str, Any] | None = None  # {"причины": [...], "перевешивает": "..."}
    session_recommendation: SessionRecommendation | None = None


class ValidationError(ValueError):
    pass


_ALLOWED_TOP_STATUSES = {HoleStatus.ПРИНЯТО, HoleStatus.В_РАБОТЕ}
_NEED_REVERSE_STATUSES = {
    SessionRecommendation.REDUCE_STAKE,
    SessionRecommendation.DELAY,
    SessionRecommendation.ABORT,
}


def validate_plan(p: Plan) -> None:
    """Бросает ValidationError при нарушении инварианта."""
    if p.version != SCHEMA_VERSION:
        raise ValidationError(f"неподдерживаемая версия схемы: {p.version}")

    seen_ids: set[str] = set()
    for h in p.дыры:
        if not HOLE_ID_PATTERN.match(h.id):
            raise ValidationError(f"формат ID '{h.id}' не соответствует H-NNN")
        if h.id in seen_ids:
            raise ValidationError(f"дублирующийся ID дыры: {h.id}")
        seen_ids.add(h.id)
        _validate_hole(h)

    for hole_id in p.топ:
        if hole_id not in seen_ids:
            raise ValidationError(f"топ ссылается на несуществующую дыру: {hole_id}")

    # Phase 3 инварианты
    hole_by_id = {h.id: h for h in p.дыры}

    # Инвариант 1: топ ≤ 3
    if len(p.топ) > 3:
        raise ValidationError(f"топ содержит более 3 дыр: {len(p.топ)}")

    # Инвариант 2: топ только на ПРИНЯТО/В_РАБОТЕ
    for hole_id in p.топ:
        h = hole_by_id[hole_id]
        if h.статус not in _ALLOWED_TOP_STATUSES:
            raise ValidationError(
                f"топ может содержать только ПРИНЯТО/В_РАБОТЕ, "
                f"{hole_id} имеет статус {h.статус.value}"
            )

    # Инвариант 3: bias_проверка только при непустом топе
    if p.bias_проверка is not None and not p.топ:
        raise ValidationError("bias_проверка указан но топ пуст")

    # Инвариант 4: reverse_премортем только при reduce_stake/delay/abort
    if p.reverse_премортем is not None:
        if p.session_recommendation is None or p.session_recommendation not in _NEED_REVERSE_STATUSES:
            raise ValidationError(
                "reverse_премортем требует session_recommendation в "
                "{reduce_stake, delay, abort}"
            )

    # Инвариант 5: 0 принятых/в-работе → топ пустой
    accepted_count = sum(1 for h in p.дыры if h.статус in _ALLOWED_TOP_STATUSES)
    if accepted_count == 0 and p.топ:
        raise ValidationError("при 0 принятых/в-работе дыр топ должен быть пустым")


def _validate_hole(h: Hole) -> None:
    if h.статус == HoleStatus.ПРИНЯТО and h.решение is None:
        raise ValidationError(f"{h.id}: статус ПРИНЯТО требует решение")
    if h.статус == HoleStatus.ОТВЕРГНУТО and not h.причина_отказа:
        raise ValidationError(f"{h.id}: статус ОТВЕРГНУТО требует причина_отказа")

    if h.режим == Mode.ПОЛНЫЙ and h.решение is not None:
        required = {"что", "почему", "prevent", "detect", "стоп_условие", "limit_damage"}
        missing = required - set(h.решение.keys())
        if missing:
            raise ValidationError(
                f"{h.id}: полный режим требует поля {sorted(missing)} в решении"
            )
    if h.режим == Mode.КРАТКИЙ and h.решение is not None:
        required = {"что", "почему", "первый_шаг", "исполнитель"}
        missing = required - set(h.решение.keys())
        if missing:
            raise ValidationError(
                f"{h.id}: краткий режим требует поля {sorted(missing)} в решении"
            )
