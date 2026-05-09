"""Parse markdown → Plan dataclass."""
from __future__ import annotations
import re
from datetime import date
from typing import Any

from scripts.frontmatter import parse_frontmatter, FrontmatterError
from scripts.plan_schema import (
    Plan, Hole, HoleStatus, Importance, Confidence, Mode,
    StatusHistoryEntry, SessionRecommendation, RerunStatus, SCHEMA_VERSION,
    ValidationError,
)


class ParseError(ValueError):
    pass


def parse_plan(text: str) -> Plan:
    """Парсит markdown-файл и возвращает Plan. Бросает ParseError при ошибке."""
    try:
        fm, body = parse_frontmatter(text)
    except FrontmatterError as e:
        raise ParseError(f"ошибка frontmatter: {e}") from e

    try:
        plan_name = fm["plan"]
        горизонт = fm["горизонт"]
        создан = _parse_date(fm["создан"])
        обновлён = _parse_date(fm["обновлён"])
        запусков = int(fm["запусков"])
        version = str(fm["version"])
    except KeyError as e:
        raise ParseError(f"отсутствует обязательное поле frontmatter: {e}") from e

    session_rec_raw = fm.get("session_recommendation")
    session_rec = SessionRecommendation(session_rec_raw) if session_rec_raw else None

    контекст = _parse_context(body)
    reference_class = _parse_reference_class(body)
    дыры = _parse_holes(body)
    топ = _parse_top_list(body)
    bias_проверка = _parse_bias(body)
    reverse_премортем = _parse_reverse(body)

    return Plan(
        plan_name=plan_name,
        горизонт=горизонт,
        создан=создан,
        обновлён=обновлён,
        запусков=запусков,
        version=version,
        контекст=контекст,
        reference_class=reference_class,
        дыры=дыры,
        топ=топ,
        bias_проверка=bias_проверка,
        reverse_премортем=reverse_премортем,
        session_recommendation=session_rec,
    )


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def _parse_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _section(body: str, header: str) -> str | None:
    r"""Вырезает содержимое секции (после заголовка до следующего ## или конца строки).

    Использует \\Z вместо $ чтобы корректно обрабатывать последнюю секцию.
    """
    pattern = rf"## {re.escape(header)}\n(.+?)(?=\n## |\Z)"
    m = re.search(pattern, body, re.DOTALL)
    return m.group(1).strip() if m else None


# ---------------------------------------------------------------------------
# Контекст
# ---------------------------------------------------------------------------

def _parse_context(body: str) -> dict[str, str]:
    section = _section(body, "Контекст")
    if not section:
        return {}
    ctx: dict[str, str] = {}
    key_map = {
        "предмет": "предмет",
        "аудитория": "аудитория",
        "успех": "успех",
        "горизонт оценки": "горизонт оценки",
    }
    for line in section.splitlines():
        line = line.strip().lstrip("- ")
        for key in key_map:
            prefix = f"{key.capitalize()}: "
            if line.startswith(prefix):
                ctx[key] = line[len(prefix):]
                break
    return ctx


def _parse_reference_class(body: str) -> list[str]:
    section = _section(body, "Контекст")
    if not section:
        return []
    for line in section.splitlines():
        line = line.strip().lstrip("- ")
        if line.startswith("Reference class: "):
            refs_str = line[len("Reference class: "):]
            return [r.strip() for r in refs_str.split(",") if r.strip()]
    return []


# ---------------------------------------------------------------------------
# Дыры
# ---------------------------------------------------------------------------

def _parse_holes(body: str) -> list[Hole]:
    """Парсит все дыры из секции ## Дыры."""
    section = _section(body, "Дыры")
    if not section:
        return []
    if section.strip() == "_(нет дыр на этом запуске)_":
        return []

    # Разбиваем по ### H-NNN: ...
    raw_holes = re.split(r"(?=### H-\d+:)", section)
    holes = []
    for raw in raw_holes:
        raw = raw.strip()
        if not raw:
            continue
        try:
            holes.append(_parse_hole(raw))
        except Exception as e:
            raise ParseError(f"ошибка парсинга дыры: {e}") from e
    return holes


def _parse_description_block(block: str) -> str:
    """Читает многострочное описание в блочном формате.

    Ожидаемый формат (новый):
        - **Описание:**
          строка 1
          строка 2

          строка 3 после пустой
    Поддерживается также устаревший инлайн-формат:
        - **Описание:** текст
    """
    # Новый блочный формат: строка "- **Описание:**" стоит отдельно
    m = re.search(
        r"^- \*\*Описание:\*\*\s*$\n(.*?)(?=^- \*\*|\Z)",
        block,
        re.MULTILINE | re.DOTALL,
    )
    if m:
        raw = m.group(1)
        out_lines = []
        for line in raw.split("\n"):
            if line.startswith("  "):
                out_lines.append(line[2:])
            elif line == "":
                out_lines.append("")
            else:
                out_lines.append(line)
        # Убираем завершающие пустые строки (граница до следующего bullet)
        while out_lines and out_lines[-1] == "":
            out_lines.pop()
        return "\n".join(out_lines)

    # Устаревший инлайн-формат (обратная совместимость)
    m_inline = re.search(r"^- \*\*Описание:\*\* (.+)$", block, re.MULTILINE)
    if m_inline:
        return m_inline.group(1).strip()
    return ""


def _parse_hole(text: str) -> Hole:
    # Заголовок ### H-NNN: title
    m = re.match(r"### (H-\d+): (.+)", text)
    if not m:
        raise ParseError(f"неверный заголовок дыры: {text[:60]!r}")
    hole_id = m.group(1)
    title = m.group(2).strip()

    def get_field(name: str) -> str | None:
        """Ищет строку `- **Name:** value` в тексте дыры."""
        pat = rf"\*\*{re.escape(name)}:\*\* (.+)"
        fm = re.search(pat, text)
        return fm.group(1).strip() if fm else None

    углы_raw = get_field("Угол зрения") or ""
    углы = [u.strip() for u in углы_raw.split(",") if u.strip()]

    найдена_raw = get_field("Найдена") or ""
    найдена_m = re.match(r"(\d{4}-\d{2}-\d{2}) \(запуск (\d+)\)", найдена_raw)
    if not найдена_m:
        raise ParseError(f"{hole_id}: не удалось распарсить поле Найдена: {найдена_raw!r}")
    найдена = date.fromisoformat(найдена_m.group(1))
    запуск_найдена = int(найдена_m.group(2))

    важность = Importance(get_field("Важность") or "")
    уверенность = Confidence(get_field("Уверенность") or "")
    статус = HoleStatus(get_field("Статус") or "")
    режим = Mode(get_field("Режим") or "")
    описание = _parse_description_block(text)
    причина_отказа = get_field("Причина отказа")

    merged_from_raw = get_field("Merged from")
    merged_from = (
        [s.strip() for s in merged_from_raw.split(",") if s.strip()]
        if merged_from_raw else []
    )

    rerun_raw = get_field("Rerun")
    rerun_status: RerunStatus | None = None
    if rerun_raw is not None:
        try:
            rerun_status = RerunStatus(rerun_raw)
        except ValueError as e:
            raise ValidationError(
                f"{hole_id}: недопустимое значение Rerun: {rerun_raw!r}. "
                f"Допустимые значения: {[s.value for s in RerunStatus]}"
            ) from e

    решение = _parse_resolution(text, режим)
    история = _parse_history(text)

    return Hole(
        id=hole_id,
        title=title,
        углы=углы,
        найдена=найдена,
        запуск_найдена=запуск_найдена,
        важность=важность,
        уверенность=уверенность,
        статус=статус,
        режим=режим,
        описание=описание,
        решение=решение,
        история_статуса=история,
        причина_отказа=причина_отказа,
        merged_from=merged_from,
        rerun_status=rerun_status,
    )


def _parse_resolution(text: str, режим: Mode) -> dict[str, Any] | None:
    """Парсит блок решения из текста дыры."""
    m = re.search(r"\*\*Решение:\*\* (.+?)(?=\n- \*\*|\Z)", text, re.DOTALL)
    if not m:
        return None

    block = m.group(0)  # начинается с "**Решение:**" (без ведущего "- ")
    lines = block.splitlines()

    # Первая строка: **Решение:** <что>
    что_m = re.match(r"\*\*Решение:\*\* (.+)", lines[0])
    что = что_m.group(1).strip() if что_m else ""

    if режим == Mode.КРАТКИЙ:
        почему = _sub_field(lines, "Почему: ")
        первый_шаг = _sub_field(lines, "Первый шаг: ")
        исполнитель = _sub_field(lines, "Исполнитель: ")
        return {
            "что": что,
            "почему": почему,
            "первый_шаг": первый_шаг,
            "исполнитель": исполнитель,
        }
    else:  # ПОЛНЫЙ
        почему = _sub_field(lines, "Зачем выбрали: ")
        исполнитель = _sub_field(lines, "Исполнитель: ")
        detect = _sub_field(lines, "Сигнал успеха (detect): ")
        стоп = _sub_field(lines, "Стоп-условие: ")
        limit = _sub_field(lines, "Если уже случилось (limit damage): ")

        # prevent — нумерованные строки внутри "Первые шаги (prevent):"
        prevent: list[str] = []
        in_prevent = False
        for line in lines[1:]:
            stripped = line.strip()
            if stripped == "- Первые шаги (prevent):":
                in_prevent = True
                continue
            if in_prevent:
                pm = re.match(r"\d+\. (.+)", stripped)
                if pm:
                    prevent.append(pm.group(1))
                elif stripped and not stripped.startswith("-"):
                    # Что-то другое — выходим
                    in_prevent = False

        # открытые_вопросы — список после "Открытые вопросы:"
        вопросы: list[str] = []
        in_questions = False
        for line in lines[1:]:
            stripped = line.strip()
            if stripped == "- Открытые вопросы:":
                in_questions = True
                continue
            if in_questions:
                qm = re.match(r"- (.+)", stripped)
                if qm:
                    вопросы.append(qm.group(1))
                elif stripped:
                    in_questions = False

        res: dict[str, Any] = {
            "что": что,
            "почему": почему,
            "prevent": prevent,
            "detect": detect,
            "стоп_условие": стоп,
            "limit_damage": limit,
            "исполнитель": исполнитель,
        }
        if вопросы:
            res["открытые_вопросы"] = вопросы
        return res


def _sub_field(lines: list[str], prefix: str) -> str:
    """Находит строку `  - <prefix><value>` и возвращает value."""
    for line in lines:
        stripped = line.strip().lstrip("- ")
        if stripped.startswith(prefix):
            return stripped[len(prefix):]
    return ""


def _parse_history(text: str) -> list[StatusHistoryEntry]:
    """Парсит блок '- **История статуса:**'."""
    m = re.search(r"\*\*История статуса:\*\*(.+?)(?=\n- \*\*|\Z)", text, re.DOTALL)
    if not m:
        return []
    entries = []
    for line in m.group(1).splitlines():
        stripped = line.strip().lstrip("- ")
        # Формат: 2026-05-09: ПРИНЯТО (запуск 1) [— комментарий]
        hm = re.match(
            r"(\d{4}-\d{2}-\d{2}): (.+?) \(запуск (\d+)\)(?:\s*—\s*(.+))?",
            stripped,
        )
        if hm:
            entries.append(StatusHistoryEntry(
                дата=date.fromisoformat(hm.group(1)),
                статус=HoleStatus(hm.group(2).strip()),
                запуск=int(hm.group(3)),
                комментарий=hm.group(4).strip() if hm.group(4) else None,
            ))
    return entries


# ---------------------------------------------------------------------------
# Топ / Bias / Reverse
# ---------------------------------------------------------------------------

def _parse_top_list(body: str) -> list[str]:
    """Парсит список ID из секции ## Топ 1–3."""
    section = _section(body, "Топ 1–3 — с чего начать")
    if not section:
        return []
    ids = []
    for line in section.splitlines():
        m = re.match(r"\d+\. \*\*(H-\d+)\*\*", line.strip())
        if m:
            ids.append(m.group(1))
    return ids


def _parse_bias(body: str) -> dict[str, str] | None:
    """Парсит блок Bias-проверки топа из секции ## Топ."""
    section = _section(body, "Топ 1–3 — с чего начать")
    if not section:
        return None
    bias_m = re.search(
        r"### Bias-проверка топа\n(.+?)(?=\n### |\Z)",
        section,
        re.DOTALL,
    )
    if not bias_m:
        return None
    bias_text = bias_m.group(1)
    риск_m = re.search(r"\*\*Главный риск искажения:\*\* (.+)", bias_text)
    корр_m = re.search(r"\*\*Коррекция:\*\* (.+)", bias_text)
    риск = риск_m.group(1).strip() if риск_m else ""
    коррекция = корр_m.group(1).strip() if корр_m else ""
    return {"риск": риск, "коррекция": коррекция}


def _parse_reverse(body: str) -> dict[str, Any] | None:
    """Парсит секцию ## Reverse премортем."""
    section = _section(body, "Reverse премортем (если запущен)")
    if not section:
        return None
    причины: list[str] = []
    перевешивает: str | None = None
    for line in section.splitlines():
        stripped = line.strip()
        nm = re.match(r"\d+\. (.+)", stripped)
        if nm:
            причины.append(nm.group(1))
        pw = re.match(r"\*\*Что перевешивает:\*\* (.+)", stripped)
        if pw:
            перевешивает = pw.group(1)
    result: dict[str, Any] = {"причины": причины}
    if перевешивает:
        result["перевешивает"] = перевешивает
    return result
