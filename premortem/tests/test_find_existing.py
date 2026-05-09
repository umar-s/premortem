import pytest
from datetime import date
from scripts.plan_schema import Plan, SCHEMA_VERSION
from scripts.plan_io import write_plan
from scripts.find_existing import find_plan, FindError


def _make(name):
    return Plan(
        plan_name=name, горизонт="через 30 дней",
        создан=date(2026, 5, 9), обновлён=date(2026, 5, 9),
        запусков=1, version=SCHEMA_VERSION,
        контекст={"предмет":"x","аудитория":"y","успех":"z","горизонт оценки":"через 30 дней"},
        reference_class=[], дыры=[],
    )


def test_find_no_files(tmp_premortem_root):
    assert find_plan(tmp_premortem_root, "anything") is None


def test_find_by_slug(tmp_premortem_root):
    write_plan(_make("My Plan"), tmp_premortem_root / "my-plan.md")
    result = find_plan(tmp_premortem_root, "My Plan")
    assert result is not None
    assert result.name == "my-plan.md"


def test_find_multiple_returns_all_options(tmp_premortem_root):
    write_plan(_make("X 1"), tmp_premortem_root / "x-1.md")
    write_plan(_make("X 2"), tmp_premortem_root / "x-2.md")
    options = find_plan(tmp_premortem_root, None, return_all=True)
    assert {o.name for o in options} == {"x-1.md", "x-2.md"}
