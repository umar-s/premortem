from scripts.slugify import slugify


def test_basic_english():
    assert slugify("My Plan") == "my-plan"


def test_russian_transliteration():
    assert slugify("Запуск Q4 2026!") == "zapusk-q4-2026"


def test_strips_punctuation():
    assert slugify("Hello, World!?") == "hello-world"


def test_collapses_dashes():
    assert slugify("a---b---c") == "a-b-c"


def test_max_length():
    s = slugify("a" * 200)
    assert len(s) <= 64


def test_empty_raises():
    import pytest
    with pytest.raises(ValueError):
        slugify("")
