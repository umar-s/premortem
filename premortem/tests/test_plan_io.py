"""Тесты атомарной записи + файлового lock'а."""
import os
import pytest
import threading
import time
from datetime import date
from pathlib import Path
from scripts.plan_schema import (
    Plan, Hole, HoleStatus, Importance, Confidence, Mode,
    StatusHistoryEntry, SCHEMA_VERSION,
)
from scripts.plan_io import write_plan, read_plan, PlanIOError


def _simple_plan():
    return Plan(
        plan_name="X", горизонт="через 30 дней",
        создан=date(2026, 5, 9), обновлён=date(2026, 5, 9),
        запусков=1, version=SCHEMA_VERSION,
        контекст={"предмет": "x", "аудитория": "y", "успех": "z",
                  "горизонт оценки": "через 30 дней"},
        reference_class=[], дыры=[],
    )


def test_write_then_read(tmp_premortem_root):
    path = tmp_premortem_root / "test.md"
    write_plan(_simple_plan(), path)
    assert path.exists()
    p2 = read_plan(path)
    assert p2.plan_name == "X"


def test_atomic_write_no_temp_left_behind(tmp_premortem_root):
    path = tmp_premortem_root / "test.md"
    write_plan(_simple_plan(), path)
    leftovers = [f.name for f in tmp_premortem_root.iterdir()
                 if f.name.startswith(".test.md") or f.suffix == ".tmp"]
    assert leftovers == []


def test_write_invalid_plan_does_not_modify_file(tmp_premortem_root):
    path = tmp_premortem_root / "test.md"
    write_plan(_simple_plan(), path)
    original = path.read_text(encoding="utf-8")

    p = _simple_plan()
    p.дыры = [Hole(
        id="BAD-1",
        title="x", углы=[], найдена=date(2026, 5, 9), запуск_найдена=1,
        важность=Importance.НИЗКАЯ, уверенность=Confidence.ПРЕДПОЛОЖЕНИЕ,
        статус=HoleStatus.ОТКРЫТА, режим=Mode.КРАТКИЙ,
        описание="x", решение=None,
    )]
    with pytest.raises(PlanIOError, match="формат ID"):
        write_plan(p, path)
    assert path.read_text(encoding="utf-8") == original


def test_read_nonexistent_raises(tmp_premortem_root):
    with pytest.raises(PlanIOError, match="не существует"):
        read_plan(tmp_premortem_root / "missing.md")


def test_lock_prevents_concurrent_writes(tmp_premortem_root):
    """Если один пишет — другой должен подождать. Конечная запись — победителя."""
    path = tmp_premortem_root / "race.md"
    write_plan(_simple_plan(), path)

    errors: list[Exception] = []

    def writer(plan_name):
        try:
            p = _simple_plan()
            p.plan_name = plan_name
            write_plan(p, path)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=writer, args=(f"P{i}",)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    final = read_plan(path)
    assert final.plan_name in {f"P{i}" for i in range(5)}
    assert errors == []


def test_stale_tmp_files_cleaned_up_on_write(tmp_premortem_root):
    """Старый .tmp файл от убитого процесса должен удалиться при следующей записи."""
    path = tmp_premortem_root / "p.md"
    write_plan(_simple_plan(), path)

    stale = tmp_premortem_root / ".p.md.dead.tmp"
    stale.write_text("оборванная запись", encoding="utf-8")
    old_time = time.time() - 86400 - 60  # на минуту старше суток
    os.utime(stale, (old_time, old_time))

    write_plan(_simple_plan(), path)

    assert not stale.exists(), "stale .tmp должен быть удалён"


def test_fresh_tmp_files_kept_on_write(tmp_premortem_root):
    """Свежий .tmp (моложе суток) не трогаем — может быть от живого параллельного процесса."""
    path = tmp_premortem_root / "p.md"
    write_plan(_simple_plan(), path)

    fresh = tmp_premortem_root / ".p.md.fresh.tmp"
    fresh.write_text("молодая запись", encoding="utf-8")

    write_plan(_simple_plan(), path)

    assert fresh.exists(), "свежий .tmp не должен трогаться (другой процесс может писать)"
