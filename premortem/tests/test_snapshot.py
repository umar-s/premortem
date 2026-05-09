from datetime import datetime
from pathlib import Path
from scripts.snapshot import save_snapshot


def test_creates_history_file(tmp_premortem_root):
    main = tmp_premortem_root / "myplan.md"
    main.write_text("# main content\n", encoding="utf-8")
    snap = save_snapshot(main, when=datetime(2026, 5, 9, 14, 32))
    assert snap.exists()
    assert snap.parent.name == "history"
    assert snap.name == "myplan-2026-05-09-1432.md"
    assert snap.read_text(encoding="utf-8") == "# main content\n"


def test_does_not_overwrite_existing_snapshot(tmp_premortem_root):
    main = tmp_premortem_root / "x.md"
    main.write_text("v1\n", encoding="utf-8")
    save_snapshot(main, when=datetime(2026, 5, 9, 14, 32))
    main.write_text("v2\n", encoding="utf-8")
    save_snapshot(main, when=datetime(2026, 5, 9, 14, 32))
    snaps = sorted((tmp_premortem_root / "history").iterdir())
    assert len(snaps) == 2
    assert snaps[0].read_text() == "v1\n"
    assert snaps[1].read_text() == "v2\n"
