"""Общие pytest-фикстуры для тестов premortem-скилла."""
import pytest
from pathlib import Path


@pytest.fixture
def tmp_premortem_root(tmp_path):
    """Временная папка docs/premortem/ для тестов I/O."""
    root = tmp_path / "docs" / "premortem"
    root.mkdir(parents=True)
    (root / "history").mkdir()
    return root


@pytest.fixture
def fixtures_dir():
    """Путь к evals/fixtures/."""
    return Path(__file__).parent.parent / "evals" / "fixtures"
