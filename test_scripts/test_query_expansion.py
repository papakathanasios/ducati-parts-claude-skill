from src.core.query_expansion import expand_query


def test_expand_translates_known_term():
    result = expand_query("Ducati exhaust", "bg")
    assert "ауспух" in result
    assert "Ducati" in result


def test_expand_keeps_model_names_untranslated():
    result = expand_query("Multistrada 1260 exhaust", "it")
    assert "Multistrada" in result
    assert "1260" in result
    assert "scarico" in result


def test_expand_unknown_term_passes_through():
    result = expand_query("Ducati foobar", "bg")
    assert "foobar" in result
    assert "Ducati" in result


def test_expand_english_returns_original():
    result = expand_query("Ducati exhaust slip on", "en")
    assert result == "Ducati exhaust slip on"


def test_expand_multiple_terms():
    result = expand_query("brake lever", "de")
    assert "Bremse" in result
    assert "Hebel" in result


def test_expand_overrides_take_precedence():
    overrides = {"bg": "custom translation"}
    result = expand_query("exhaust", "bg", overrides=overrides)
    assert result == "custom translation"


def test_expand_case_insensitive_matching():
    result = expand_query("Ducati Exhaust", "it")
    assert "scarico" in result
