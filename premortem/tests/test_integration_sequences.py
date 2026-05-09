"""Integration: последовательности read/write сохраняют валидность."""
import pytest
from scripts.plan_io import read_plan, write_plan


pytestmark = pytest.mark.integration


@pytest.mark.parametrize("fixture_name", [
    "new.md", "after-run-1.md", "after-run-2.md", "with-reverse-premortem.md",
])
def test_fixture_round_trips_through_io(tmp_premortem_root, fixtures_dir, fixture_name):
    src = fixtures_dir / fixture_name
    dst = tmp_premortem_root / fixture_name
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    p = read_plan(dst)
    write_plan(p, dst)
    p2 = read_plan(dst)

    assert p2.plan_name == p.plan_name
    assert len(p2.дыры) == len(p.дыры)
    for h1, h2 in zip(p.дыры, p2.дыры):
        assert h1.id == h2.id
        assert h1.статус == h2.статус
        assert h1.режим == h2.режим


def test_three_writes_keep_file_valid(tmp_premortem_root, fixtures_dir):
    src = fixtures_dir / "after-run-1.md"
    dst = tmp_premortem_root / "test.md"
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    p_initial = read_plan(dst)

    for _ in range(3):
        p = read_plan(dst)
        write_plan(p, dst)

    p_final = read_plan(dst)
    assert p_final.plan_name == p_initial.plan_name
    assert len(p_final.дыры) == len(p_initial.дыры)
    assert [h.id for h in p_final.дыры] == [h.id for h in p_initial.дыры]
    for h_init, h_final in zip(p_initial.дыры, p_final.дыры):
        assert len(h_final.история_статуса) == len(h_init.история_статуса), \
            f"{h_init.id}: история не должна расти на повторных write"
