"""Единый CLI-вход. Subcommands: slugify, classify, validate-helper, next-id, stats,
read, write, snapshot, find, dedup."""
# /// script
# dependencies = ["pyyaml>=6.0", "jsonschema>=4.0", "click>=8.0"]
# ///
from __future__ import annotations
import sys
from pathlib import Path

# Позволяет запускать `python scripts/cli.py ...` из любого cwd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import click


@click.group()
def cli():
    """premortem CLI — детерминированная механика для SKILL.md."""


@cli.command()
@click.argument("text")
def slugify(text: str):
    """Привести имя плана к safe filename slug."""
    from scripts.slugify import slugify as _s
    click.echo(_s(text))


@cli.command()
@click.argument("plan_text")
def classify(plan_text: str):
    """Классификатор углов: текст плана → JSON {profile, angles, confidence, ...}."""
    from scripts.classify_angles import classify as _c
    r = _c(plan_text)
    click.echo(json.dumps({
        "profile": r.profile, "angles": r.angles,
        "confidence": r.confidence, "matched_keywords": r.matched_keywords,
        "reason": r.reason,
    }, ensure_ascii=False))


@cli.command("validate-helper")
def validate_helper():
    """Валидировать JSON ответ помощника (читает из stdin)."""
    from scripts.validate_helper_response import validate, HelperResponseError
    data = json.load(sys.stdin)
    try:
        validate(data)
        click.echo("ok")
    except HelperResponseError as e:
        click.echo(f"validation error: {e}", err=True)
        sys.exit(1)


@cli.command("next-id")
@click.option("--existing", required=True, help="Comma-separated existing IDs (H-001,H-002,...)")
def next_id(existing: str):
    """Следующий доступный H-NNN ID."""
    from scripts.id_counter import next_id as _n
    ids = [s.strip() for s in existing.split(",") if s.strip()]
    click.echo(_n(ids))


@cli.command()
@click.argument("path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def stats(path: Path):
    """Статистика по плану: счёт дыр по статусам."""
    from scripts.plan_io import read_plan
    from scripts.stats import summarize
    p = read_plan(path)
    click.echo(json.dumps(summarize(p), ensure_ascii=False))


@cli.command()
@click.argument("path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def read(path: Path):
    """Прочитать план, вывести JSON-сериализацию."""
    from scripts.plan_io import read_plan
    from scripts.plan_serialize import plan_to_json
    p = read_plan(path)
    click.echo(plan_to_json(p))


@cli.command()
@click.option("--plan-json", "plan_json_path",
              type=click.Path(exists=True, dir_okay=False, path_type=Path), required=True)
@click.option("--path", type=click.Path(path_type=Path), required=True)
def write(plan_json_path: Path, path: Path):
    """Записать план из JSON-файла в md (атомарно с lock)."""
    from scripts.plan_io import write_plan
    from scripts.plan_serialize import plan_from_json
    raw = plan_json_path.read_text(encoding="utf-8")
    p = plan_from_json(raw)
    write_plan(p, path)


@cli.command()
@click.argument("path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def snapshot(path: Path):
    """Сохранить снимок плана в history/."""
    from scripts.snapshot import save_snapshot
    snap = save_snapshot(path)
    click.echo(str(snap))


@cli.command()
@click.argument("root", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--name", default=None)
def find(root: Path, name: str | None):
    """Найти существующий план в docs/premortem/ по имени."""
    from scripts.find_existing import find_plan
    result = find_plan(root, name)
    click.echo(str(result) if result else "")


@cli.command()
def dedup():
    """Hash-дедуп дыр (читает JSON-список из stdin)."""
    from scripts.hole_dedup import dedup_by_hash
    data = json.load(sys.stdin)
    click.echo(json.dumps(dedup_by_hash(data), ensure_ascii=False))


if __name__ == "__main__":
    cli()
