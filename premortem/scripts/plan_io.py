"""Атомарная запись + advisory file lock через fcntl."""
from __future__ import annotations
import fcntl
import os
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from scripts.plan_schema import Plan, validate_plan, ValidationError
from scripts.plan_render import render_plan
from scripts.plan_parse import parse_plan, ParseError


_STALE_TMP_AGE_SECONDS = 86400


class PlanIOError(IOError):
    pass


def _fsync_dir(path: Path) -> None:
    """fsync на каталог чтобы запись rename'а пережила crash."""
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _cleanup_stale_tmps(path: Path) -> None:
    """Удаляет .{name}.*.tmp файлы старше суток (после kill -9 во время записи)."""
    now = time.time()
    pattern = f".{path.name}.*.tmp"
    for tmp in path.parent.glob(pattern):
        try:
            if now - tmp.stat().st_mtime > _STALE_TMP_AGE_SECONDS:
                tmp.unlink()
        except OSError:
            pass


@contextmanager
def _locked(lock_path: Path):
    """Advisory exclusive lock через fcntl.

    Lockfile НЕ удаляется в конце — race condition: между unlink и flock другого
    процесса он может пытаться открыть несуществующий файл. Файл малый, не растёт.
    """
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _write_locked(text: str, path: Path) -> None:
    """Атомарная запись через tempfile + os.replace + fsync. Без lock'а.

    Вызывается только внутри уже взятого _locked(). Не для прямого
    использования вне этого модуля.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    _cleanup_stale_tmps(path)
    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
        _fsync_dir(path.parent)
    except Exception:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


def write_plan(plan: Plan, path: str | Path) -> None:
    """Атомарная запись с валидацией. При невалидном плане файл не трогается."""
    path = Path(path)
    try:
        validate_plan(plan)
    except ValidationError as e:
        raise PlanIOError(str(e)) from e

    text = render_plan(plan)
    lock_path = path.with_suffix(path.suffix + ".lock")

    with _locked(lock_path):
        _write_locked(text, path)


def read_plan(path: str | Path) -> Plan:
    """Читает план из файла под advisory lock'ом."""
    path = Path(path)
    if not path.exists():
        raise PlanIOError(f"файл не существует: {path}")

    lock_path = path.with_suffix(path.suffix + ".lock")

    with _locked(lock_path):
        text = path.read_text(encoding="utf-8")

        try:
            plan = parse_plan(text)
        except ParseError as e:
            raise PlanIOError(f"парсинг: {e}") from e
        try:
            validate_plan(plan)
        except ValidationError as e:
            raise PlanIOError(f"валидация: {e}") from e

    return plan
