from decimal import Decimal
from src.core.shipping import ShippingEstimator


def test_estimate_shipping_bulgaria():
    estimator = ShippingEstimator(destination_postal="15562", destination_country="GR")
    low, high = estimator.estimate("BG")
    assert low == Decimal("5")
    assert high == Decimal("10")


def test_estimate_shipping_germany():
    estimator = ShippingEstimator(destination_postal="15562", destination_country="GR")
    low, high = estimator.estimate("DE")
    assert low == Decimal("10")
    assert high == Decimal("20")


def test_estimate_shipping_uk():
    estimator = ShippingEstimator(destination_postal="15562", destination_country="GR")
    low, high = estimator.estimate("GB")
    assert low == Decimal("15")
    assert high == Decimal("30")


def test_is_eu():
    estimator = ShippingEstimator(destination_postal="15562", destination_country="GR")
    assert estimator.is_eu("BG") is True
    assert estimator.is_eu("IT") is True
    assert estimator.is_eu("GB") is False
    assert estimator.is_eu("US") is False


def test_midpoint_estimate():
    estimator = ShippingEstimator(destination_postal="15562", destination_country="GR")
    mid = estimator.midpoint("RO")
    assert mid == Decimal("9")
