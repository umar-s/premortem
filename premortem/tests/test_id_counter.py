from scripts.id_counter import next_id, max_id


def test_next_id_first():
    assert next_id([]) == "H-001"


def test_next_id_after_existing():
    assert next_id(["H-001", "H-002", "H-005"]) == "H-006"


def test_next_id_handles_gaps():
    assert next_id(["H-001", "H-003"]) == "H-004"


def test_max_id_basic():
    assert max_id(["H-001", "H-005", "H-003"]) == 5


def test_max_id_empty():
    assert max_id([]) == 0


def test_pads_to_min_3_digits():
    assert next_id([f"H-{i:03d}" for i in range(1, 1000)]) == "H-1000"
