"""Switch-классификатор углов по типу плана. LLM-fallback при низкой уверенности."""
from __future__ import annotations
import re
from dataclasses import dataclass


_CRITICAL_BASE = ["Клиент", "Исполнитель", "Противник", "Допущения"]
_FUTURE_ANGLE = "Будущий поддерживающий"


def _pat(pattern: str) -> re.Pattern:
    """Компилирует паттерн с флагом IGNORECASE.

    Не используем \\b для кириллицы — стандартные word boundaries не работают
    с Unicode-символами за пределами ASCII. Паттерны и так достаточно специфичны.
    """
    return re.compile(pattern, re.I | re.UNICODE)


_PROFILES: list[tuple[str, list[re.Pattern], list[str]]] = [
    ("product_launch",
     [_pat(r"(?:launch|запуск|релиз|релиза|GA|beta|воркшоп)")],
     ["Конкурент", "Ценообразование"]),
    ("pricing_change",
     [_pat(r"(?:price|pricing|цен[ауыое]?|тариф)")],
     ["Существующие клиенты", "Churn"]),
    ("hire",
     [_pat(r"(?:hire|найм|нанима[ею]|вакансия|candidate|кандидат)")],
     ["Культура команды", "Runway"]),
    ("tech_project",
     [_pat(r"(?:refactor|migration|миграци[яи]|архитектур|рефакторинг)")],
     ["Архитектура", "Эксплуатация"]),
    ("strategic_pivot",
     [_pat(r"(?:pivot|поворот|стратегич|новое направление|разворот|market shift)")],
     ["Рынок", "Тайминг"]),
    ("personal_decision",
     [_pat(r"(?:should I|стоит ли мне|уйти из компании|личн[оы])")],
     ["Будущий-ты-через-N-лет"]),
]


@dataclass
class ClassifyResult:
    profile: str
    angles: list[str]
    confidence: float
    matched_keywords: list[str]
    reason: str


def _select_angles(situational: list[str]) -> list[str]:
    """6 углов: 4 критичных + 1 ситуативный + "Будущий поддерживающий" (sacred для WYSIATI).

    Лимит 1 ситуативный — чтобы получалось ровно 6 углов на 3 помощника = (2,2,2).
    """
    unique_situational = [
        s for s in situational
        if s not in _CRITICAL_BASE and s != _FUTURE_ANGLE
    ][:1]
    return list(_CRITICAL_BASE) + unique_situational + [_FUTURE_ANGLE]


def classify(plan_text: str) -> ClassifyResult:
    """Жадный матч: первый сработавший профиль выигрывает.

    Уверенность = базовая 0.5 + 0.2 за каждый сработавший паттерн (max 1.0).
    Default fallback — confidence 0.3.
    """
    for profile, patterns, situational in _PROFILES:
        matches = []
        for p in patterns:
            m = p.search(plan_text)
            if m:
                matches.append(m.group(0))
        if matches:
            angles = _select_angles(situational)
            confidence = min(1.0, 0.5 + 0.2 * len(matches))
            return ClassifyResult(
                profile=profile, angles=angles,
                confidence=confidence, matched_keywords=matches,
                reason=f"matched profile '{profile}' on keywords {matches}",
            )
    return ClassifyResult(
        profile="default", angles=_select_angles(["Конкурент", "Тайминг"]),
        confidence=0.3, matched_keywords=[],
        reason="no profile matched, used default base+competitor+timing",
    )
