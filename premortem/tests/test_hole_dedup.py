from scripts.hole_dedup import hash_description, dedup_by_hash


def test_hash_normalizes_whitespace():
    h1 = hash_description("Hello   World\n")
    h2 = hash_description("Hello World")
    assert h1 == h2


def test_hash_normalizes_case():
    assert hash_description("HELLO") == hash_description("hello")


def test_dedup_keeps_first_of_each():
    items = [
        {"описание": "Дыра A"},
        {"описание": "дыра a "},
        {"описание": "Дыра B"},
    ]
    result = dedup_by_hash(items, key="описание")
    assert len(result) == 2
    assert result[0]["описание"] == "Дыра A"
    assert result[1]["описание"] == "Дыра B"
