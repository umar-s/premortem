from scripts.classify_angles import classify, ClassifyResult


def test_product_launch_profile():
    r = classify("Запуск платного воркшопа в Q4")
    assert r.profile == "product_launch"
    assert "Конкурент" in r.angles
    assert "Будущий поддерживающий" in r.angles
    assert r.confidence >= 0.7


def test_pricing_change_profile():
    r = classify("Меняю цену с $99 на $149")
    assert r.profile == "pricing_change"
    assert "Существующие клиенты" in r.angles
    assert "Будущий поддерживающий" in r.angles


def test_hire_profile():
    r = classify("Нанимаю senior backend engineer")
    assert r.profile == "hire"
    assert "Культура команды" in r.angles
    assert "Будущий поддерживающий" in r.angles


def test_tech_project_profile():
    r = classify("Миграция базы данных с MySQL на Postgres")
    assert r.profile == "tech_project"
    assert "Архитектура" in r.angles
    assert "Будущий поддерживающий" in r.angles


def test_personal_decision():
    r = classify("Стоит ли мне уйти из компании и начать своё")
    assert r.profile == "personal_decision"
    assert "Будущий-ты-через-N-лет" in r.angles
    assert "Будущий поддерживающий" in r.angles


def test_default_fallback_low_confidence():
    r = classify("Что-то совсем непонятное")
    assert r.profile == "default"
    assert r.confidence < 0.5
    assert "Конкурент" in r.angles
    assert "Будущий поддерживающий" in r.angles


def test_strategic_pivot_profile():
    r = classify("Поворот в стратегии — pivot к новой нише")
    assert r.profile == "strategic_pivot"
    assert "Рынок" in r.angles
    assert "Будущий поддерживающий" in r.angles


def test_angle_count_exactly_6_no_duplicates():
    """6 углов на 3 помощника = (2,2,2). Без дублей."""
    for plan in ("Запуск X", "Найм Y", "Что-то", "Миграция базы", "Pricing change"):
        r = classify(plan)
        assert len(r.angles) == 6
        assert len(set(r.angles)) == 6


def test_critical_base_angles_always_present():
    """Клиент / Исполнитель / Противник / Допущения — должны быть всегда."""
    critical = {"Клиент", "Исполнитель", "Противник", "Допущения"}
    for plan in ("Запуск воркшопа", "Найм senior", "Pricing", "Миграция", "Что-то"):
        r = classify(plan)
        assert critical.issubset(set(r.angles)), f"{plan}: missing {critical - set(r.angles)}"


def test_future_angle_always_present():
    """'Будущий поддерживающий' sacred — обязателен для WYSIATI-микрошага."""
    for plan in ("Запуск", "Найм", "Pricing", "Pivot", "Стоит ли мне", "Что-то", "Миграция"):
        r = classify(plan)
        assert "Будущий поддерживающий" in r.angles, f"{plan}: missing future angle"


def test_situational_angles_present_when_profile_matches():
    r = classify("Меняю цену на тариф")
    assert "Существующие клиенты" in r.angles
