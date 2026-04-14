from decimal import Decimal
from src.core.currency import CurrencyConverter


def test_convert_eur_to_eur():
    converter = CurrencyConverter()
    converter._rates = {"EUR": Decimal("1")}
    result = converter.convert(Decimal("100"), "EUR")
    assert result == Decimal("100")


def test_convert_bgn_to_eur():
    converter = CurrencyConverter()
    converter._rates = {"BGN": Decimal("1.9558")}
    result = converter.convert(Decimal("19.558"), "BGN")
    assert result == Decimal("10.00")


def test_convert_pln_to_eur():
    converter = CurrencyConverter()
    converter._rates = {"PLN": Decimal("4.30")}
    result = converter.convert(Decimal("43.00"), "PLN")
    assert result == Decimal("10.00")


def test_convert_unknown_currency_raises():
    converter = CurrencyConverter()
    converter._rates = {}
    try:
        converter.convert(Decimal("100"), "XYZ")
        assert False, "Should have raised"
    except KeyError:
        pass


def test_supported_currencies():
    converter = CurrencyConverter()
    converter._rates = {
        "BGN": Decimal("1.96"), "RON": Decimal("4.97"),
        "HUF": Decimal("395"), "PLN": Decimal("4.30"),
        "CZK": Decimal("25.30"), "GBP": Decimal("0.86"),
    }
    assert converter.is_supported("BGN") is True
    assert converter.is_supported("EUR") is True
    assert converter.is_supported("XYZ") is False
