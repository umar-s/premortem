"""Тесты CLI-обёртки. Проверяем контракт I/O, не логику (она в test_*.py)."""
import json
import subprocess
import sys
from pathlib import Path
import pytest


CLI = Path(__file__).parent.parent / "scripts" / "cli.py"


def _run(*args, input_text=None):
    """Запускает CLI напрямую через python (без uv run — внутри теста)."""
    cmd = [sys.executable, str(CLI), *args]
    return subprocess.run(
        cmd, input=input_text, capture_output=True, text=True, check=False,
    )


def test_slugify_command():
    r = _run("slugify", "My Plan")
    assert r.returncode == 0
    assert r.stdout.strip() == "my-plan"


def test_slugify_russian():
    r = _run("slugify", "Запуск Q4 2026!")
    assert r.returncode == 0
    assert r.stdout.strip() == "zapusk-q4-2026"


def test_classify_command():
    r = _run("classify", "Запуск воркшопа")
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data["profile"] == "product_launch"
    assert len(data["angles"]) == 6


def test_validate_helper_valid_input():
    payload = json.dumps({
        "holes": [{
            "title": "test hole title",
            "описание": "длинное описание дыры на двадцать символов минимум",
            "почему_важно": "одна фраза о важности",
            "важность": "высокая",
            "уверенность": "подкреплено контекстом",
            "источник_угол": "Клиент",
        }]
    })
    r = _run("validate-helper", input_text=payload)
    assert r.returncode == 0


def test_validate_helper_invalid_input():
    payload = '{"holes": [{"title": "x"}]}'  # incomplete
    r = _run("validate-helper", input_text=payload)
    assert r.returncode != 0
    assert "error" in r.stderr.lower() or len(r.stderr) > 0


def test_next_id_command():
    r = _run("next-id", "--existing", "H-001,H-005")
    assert r.returncode == 0
    assert r.stdout.strip() == "H-006"


def test_stats_command(tmp_path, fixtures_dir):
    src = fixtures_dir / "after-run-1.md"
    target = tmp_path / "x.md"
    target.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    r = _run("stats", str(target))
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data["всего"] == 2
    assert data["принято"] == 1


def test_unknown_command_returns_nonzero():
    r = _run("nonsense-command")
    assert r.returncode != 0


def test_read_write_round_trip(tmp_path, fixtures_dir):
    """read → JSON → write возвращает план с теми же id/статусом дыр."""
    src = fixtures_dir / "after-run-1.md"
    src_md = tmp_path / "src.md"
    src_md.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    r1 = _run("read", str(src_md))
    assert r1.returncode == 0, r1.stderr
    plan_json = tmp_path / "plan.json"
    plan_json.write_text(r1.stdout, encoding="utf-8")

    dst_md = tmp_path / "dst.md"
    r2 = _run("write", "--plan-json", str(plan_json), "--path", str(dst_md))
    assert r2.returncode == 0, r2.stderr
    assert dst_md.exists()

    r3 = _run("read", str(dst_md))
    assert r3.returncode == 0, r3.stderr
    a = json.loads(r1.stdout)
    b = json.loads(r3.stdout)
    assert a["plan_name"] == b["plan_name"]
    assert [h["id"] for h in a["дыры"]] == [h["id"] for h in b["дыры"]]
    assert [h["статус"] for h in a["дыры"]] == [h["статус"] for h in b["дыры"]]


def test_write_with_missing_json_fails():
    """--plan-json указывает на несуществующий файл → click clean error, не traceback."""
    r = _run("write", "--plan-json", "/nonexistent/plan.json", "--path", "/tmp/out.md")
    assert r.returncode != 0
    assert "does not exist" in r.stderr.lower() or "not exist" in r.stderr.lower()
