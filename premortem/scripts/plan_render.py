"""Рендер Plan dataclass → markdown."""
from __future__ import annotations
from scripts.plan_schema import (
    Plan, Hole, HoleStatus, Mode, StatusHistoryEntry,
)
from scripts.frontmatter import render_frontmatter


def render_plan(p: Plan) -> str:
    """Полный md-файл из Plan."""
    fm = {
        "plan": p.plan_name,
        "горизонт": p.горизонт,
        "создан": p.создан,
        "обновлён": p.обновлён,
        "запусков": p.запусков,
        "version": p.version,
    }
    if p.session_recommendation is not None:
        fm["session_recommendation"] = p.session_recommendation.value
    body = _render_body(p)
    return render_frontmatter(fm, body)


def _render_body(p: Plan) -> str:
    parts = [f"# Премортем: {p.plan_name}\n"]
    parts.append(_render_context(p))
    parts.append(_render_holes(p))
    if p.топ:
        parts.append(_render_top(p))
    if p.reverse_премортем:
        parts.append(_render_reverse(p))
    parts.append(_render_resolved(p))
    return "\n".join(parts)


def _render_context(p: Plan) -> str:
    lines = ["## Контекст"]
    for key in ("предмет", "аудитория", "успех", "горизонт оценки"):
        if key in p.контекст:
            lines.append(f"- {key.capitalize()}: {p.контекст[key]}")
    if p.reference_class:
        lines.append(f"- Reference class: {', '.join(p.reference_class)}")
    return "\n".join(lines) + "\n"


def _render_holes(p: Plan) -> str:
    if not p.дыры:
        return "## Дыры\n\n_(нет дыр на этом запуске)_\n"
    parts = ["## Дыры\n"]
    for h in p.дыры:
        parts.append(_render_hole(h))
    return "\n".join(parts)


def _render_hole(h: Hole) -> str:
    lines = [f"### {h.id}: {h.title}"]
    lines.append(f"- **Угол зрения:** {', '.join(h.углы)}")
    lines.append(f"- **Найдена:** {h.найдена.isoformat()} (запуск {h.запуск_найдена})")
    lines.append(f"- **Важность:** {h.важность.value}")
    lines.append(f"- **Уверенность:** {h.уверенность.value}")
    lines.append(f"- **Статус:** {h.статус.value}")
    lines.append(f"- **Режим:** {h.режим.value}")
    desc_lines = h.описание.split("\n")
    lines.append("- **Описание:**")
    for desc_line in desc_lines:
        lines.append(f"  {desc_line}" if desc_line else "")
    if h.решение:
        lines.append(_render_resolution(h))
    if h.merged_from:
        lines.append(f"- **Merged from:** {', '.join(h.merged_from)}")
    if h.rerun_status is not None:
        lines.append(f"- **Rerun:** {h.rerun_status.value}")
    if h.причина_отказа:
        lines.append(f"- **Причина отказа:** {h.причина_отказа}")
    if h.история_статуса:
        lines.append("- **История статуса:**")
        for entry in h.история_статуса:
            comment = f" — {entry.комментарий}" if entry.комментарий else ""
            lines.append(
                f"  - {entry.дата.isoformat()}: {entry.статус.value} "
                f"(запуск {entry.запуск}){comment}"
            )
    return "\n".join(lines) + "\n"


def _render_resolution(h: Hole) -> str:
    r = h.решение or {}
    lines = [f"- **Решение:** {r.get('что', '')}"]
    if h.режим == Mode.КРАТКИЙ:
        lines.append(f"  - Почему: {r.get('почему', '')}")
        lines.append(f"  - Первый шаг: {r.get('первый_шаг', '')}")
        lines.append(f"  - Исполнитель: {r.get('исполнитель', '')}")
    else:  # ПОЛНЫЙ
        lines.append(f"  - Зачем выбрали: {r.get('почему', '')}")
        lines.append("  - Первые шаги (prevent):")
        for i, step in enumerate(r.get("prevent", []), 1):
            lines.append(f"    {i}. {step}")
        lines.append(f"  - Исполнитель: {r.get('исполнитель', '')}")
        lines.append(f"  - Сигнал успеха (detect): {r.get('detect', '')}")
        lines.append(f"  - Стоп-условие: {r.get('стоп_условие', '')}")
        lines.append(f"  - Если уже случилось (limit damage): {r.get('limit_damage', '')}")
        if r.get("открытые_вопросы"):
            lines.append("  - Открытые вопросы:")
            for q in r["открытые_вопросы"]:
                lines.append(f"    - {q}")
    return "\n".join(lines)


def _render_top(p: Plan) -> str:
    lines = ["## Топ 1–3 — с чего начать"]
    for i, hid in enumerate(p.топ, 1):
        h = next((x for x in p.дыры if x.id == hid), None)
        first_step = ""
        if h and h.решение:
            first_step = h.решение.get("первый_шаг") or (
                h.решение.get("prevent", [""])[0] if h.режим == Mode.ПОЛНЫЙ else ""
            )
        title = h.title if h else "?"
        lines.append(f"{i}. **{hid}** — {title}. Первый шаг: {first_step}")
    if p.bias_проверка:
        lines.append("")
        lines.append("### Bias-проверка топа")
        lines.append(f"- **Главный риск искажения:** {p.bias_проверка.get('риск', '')}")
        lines.append(f"- **Коррекция:** {p.bias_проверка.get('коррекция', '')}")
    return "\n".join(lines) + "\n"


def _render_reverse(p: Plan) -> str:
    r = p.reverse_премортем or {}
    lines = ["## Reverse премортем (если запущен)"]
    lines.append("*Заполняется только если финальная рекомендация — отложить/отказаться.*\n")
    lines.append("«Прошёл горизонт. Не сделали. Оказалось зря — почему?»")
    for i, reason in enumerate(r.get("причины", []), 1):
        lines.append(f"{i}. {reason}")
    if r.get("перевешивает"):
        lines.append("")
        lines.append(f"**Что перевешивает:** {r['перевешивает']}")
    return "\n".join(lines) + "\n"


def _render_resolved(p: Plan) -> str:
    resolved = [h for h in p.дыры if h.статус == HoleStatus.ЗАКРЫТА]
    if not resolved:
        return ""
    lines = ["## Закрытые дыры (resolved)"]
    for h in resolved:
        lines.append(f"- {h.id}: {h.title}")
    return "\n".join(lines) + "\n"
