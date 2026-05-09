"""Тесты YAML frontmatter parse/write."""
import pytest
from datetime import date
from scripts.frontmatter import parse_frontmatter, render_frontmatter, FrontmatterError


def test_parse_minimal_frontmatter():
    text = """---
plan: My Plan
горизонт: через 3 месяца
создан: 2026-05-09
обновлён: 2026-05-09
запусков: 1
version: '1.0'
---
# Body

content here
"""
    fm, body = parse_frontmatter(text)
    assert fm["plan"] == "My Plan"
    assert fm["горизонт"] == "через 3 месяца"
    assert fm["создан"] == date(2026, 5, 9)
    assert fm["запусков"] == 1
    assert fm["version"] == "1.0"
    assert body.startswith("# Body\n")


def test_render_then_parse_preserves_data():
    fm = {
        "plan": "X",
        "горизонт": "после пилота",
        "создан": date(2026, 5, 9),
        "обновлён": date(2026, 8, 15),
        "запусков": 2,
        "version": "1.0",
    }
    body = "# Premortem: X\n\nbody\n"
    text = render_frontmatter(fm, body)
    fm2, body2 = parse_frontmatter(text)
    assert fm2 == fm
    assert body2 == body


def test_parse_missing_frontmatter_raises():
    with pytest.raises(FrontmatterError, match="не найден frontmatter"):
        parse_frontmatter("# Just a body\n")


def test_parse_unclosed_frontmatter_raises():
    with pytest.raises(FrontmatterError, match="не закрыт"):
        parse_frontmatter("---\nplan: X\n# body\n")


def test_render_preserves_key_order():
    fm = {"plan": "X", "горизонт": "y", "создан": date(2026, 5, 9),
          "обновлён": date(2026, 5, 9), "запусков": 1, "version": "1.0"}
    text = render_frontmatter(fm, "")
    lines = [l for l in text.splitlines() if ":" in l]
    keys = [l.split(":")[0].strip() for l in lines]
    assert keys == ["plan", "горизонт", "создан", "обновлён", "запусков", "version"]


def test_parse_empty_body_returns_empty_string():
    text = "---\nplan: X\nversion: '1.0'\n---\n"
    fm, body = parse_frontmatter(text)
    assert fm["plan"] == "X"
    assert fm["version"] == "1.0"
    assert body == ""


def test_parse_no_trailing_newline_after_close_raises():
    # Парсер требует \n---\n; файл, обрезанный до последнего `-` без \n,
    # трактуется как незакрытый frontmatter. Мы всегда пишем через atomic_write,
    # который добавляет финальный перевод строки, поэтому на практике такого
    # не возникает. Тест документирует это ограничение.
    text = "---\nplan: X\nversion: '1.0'\n---"
    with pytest.raises(FrontmatterError, match="не закрыт"):
        parse_frontmatter(text)
